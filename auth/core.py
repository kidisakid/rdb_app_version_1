"""
Authentication module — MongoDB-backed login with role-based access control.
Roles: "admin" (all tools + user management) | "user" (pipeline + merge only)
"""

import base64
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

import bcrypt
import streamlit as st
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, DuplicateKeyError, ServerSelectionTimeoutError


# ── Security policy constants ───────────────────────────────────────
MIN_PASSWORD_LENGTH = 8
MAX_FAILED_ATTEMPTS = 5            # login + change-password both use this
LOCKOUT_MINUTES = 15               # lockout window after hitting the limit
GENERIC_LOGIN_ERROR = "Invalid username or password."
GENERIC_CHANGE_ERROR = "Invalid username or current password."
LOCKOUT_ERROR = "Account temporarily locked. Try again later."


# ── MongoDB connection ──────────────────────────────────────────────

@st.cache_resource
def _get_mongo_client():
    """Cached MongoDB client (one per app lifetime)."""
    uri = st.secrets["mongo"]["uri"]
    client = MongoClient(
        uri,
        serverSelectionTimeoutMS=10000,
        connectTimeoutMS=10000,
        socketTimeoutMS=10000,
    )
    client.admin.command("ping")

    db_name = st.secrets["mongo"]["db_name"]
    client[db_name]["users"].create_index("username", unique=True)

    return client


def _get_users_collection():
    client = _get_mongo_client()
    db_name = st.secrets["mongo"]["db_name"]
    return client[db_name]["users"]


def _get_events_collection():
    """Audit log collection. Kept separate from users for clean reads and retention."""
    client = _get_mongo_client()
    db_name = st.secrets["mongo"]["db_name"]
    return client[db_name]["security_events"]


def _log_security_event(event: str, username: str, actor: str, success: bool) -> None:
    """Best-effort audit log write. Never raises — logging must not break auth."""
    try:
        _get_events_collection().insert_one({
            "event": event,
            "username": username,
            "actor": actor,
            "success": bool(success),
            "timestamp": datetime.now(timezone.utc),
        })
    except Exception:
        # Logging failures must never block a security-critical code path.
        pass


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _is_locked(user: dict, lock_field: str) -> bool:
    """Return True if the user doc has an active lockout on the given field."""
    lock_until = user.get(lock_field)
    if not lock_until:
        return False
    # Mongo returns naive datetimes for legacy docs — treat them as UTC.
    if isinstance(lock_until, datetime) and lock_until.tzinfo is None:
        lock_until = lock_until.replace(tzinfo=timezone.utc)
    return isinstance(lock_until, datetime) and lock_until > _utcnow()


# ── Password helpers ────────────────────────────────────────────────

def _hash_password(password: str) -> bytes:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())


def _verify_password(password: str, hashed: bytes) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), hashed)


def _validate_password(password: str, username: str | None = None) -> list[str]:
    """Return a list of unmet password requirements. Empty list means OK."""
    issues: list[str] = []
    if not isinstance(password, str):
        return [f"at least {MIN_PASSWORD_LENGTH} characters"]
    if len(password) < MIN_PASSWORD_LENGTH:
        issues.append(f"at least {MIN_PASSWORD_LENGTH} characters")
    if username and isinstance(username, str) and password.strip().lower() == username.strip().lower():
        issues.append("something different from your username")
    return issues


# ── User operations ─────────────────────────────────────────────────

def register_user(username: str, password: str, role: str = "user") -> tuple[bool, str]:
    """Register a new user — admin-only action. Returns (success, message)."""
    # Server-side guard: only admins may create accounts
    if not is_admin():
        return False, "Permission denied. Only admins can create accounts."
    # Only super admins can create super admin accounts
    if role == "super_admin" and not is_super_admin():
        return False, "Permission denied. Only super admins can create super admin accounts."

    username = username.strip()
    if len(username) < 3:
        return False, "Username must be at least 3 characters."
    issues = _validate_password(password, username=username)
    if issues:
        return False, f"Password must contain: {', '.join(issues)}."
    if not re.match(r"^[a-zA-Z0-9_]+$", username):
        return False, "Username can only contain letters, numbers, and underscores."
    if role not in ("admin", "user", "super_admin"):
        return False, "Invalid role."

    try:
        users = _get_users_collection()
        users.insert_one({
            "username": username.lower(),
            "display_name": username,
            "password": _hash_password(password),
            "role": role,
        })
        return True, f"User '{username}' created successfully."
    except DuplicateKeyError:
        return False, "Username already taken."
    except (ConnectionFailure, ServerSelectionTimeoutError):
        return False, "Could not connect to database. Please try again later."


def authenticate_user(username: str, password: str) -> tuple[bool, str, str]:
    """Authenticate a user. Returns (success, display_name | error, role).

    Hardening:
    - Lockout after MAX_FAILED_ATTEMPTS consecutive failures (LOCKOUT_MINUTES).
    - Same generic error for "no such user" and "wrong password" to prevent
      username enumeration.
    - Writes a security_events audit record for every attempt.
    - Propagates the `must_change_password` flag into session state so the
      main router can force a password change on the next page render.
    """
    # Guard: reject non-string inputs (prevents NoSQL operator injection)
    if not isinstance(username, str) or not isinstance(password, str):
        return False, "Invalid input.", ""
    username = username.strip().lower()[:100]
    if not username:
        return False, GENERIC_LOGIN_ERROR, ""
    try:
        users = _get_users_collection()
        user = users.find_one({"username": username})
        if not user:
            _log_security_event("login", username, actor=username, success=False)
            return False, GENERIC_LOGIN_ERROR, ""

        # Lockout check (before verifying the password so an attacker cannot
        # distinguish "locked" from "wrong password" by timing).
        if _is_locked(user, "locked_until"):
            _log_security_event("login_locked", username, actor=username, success=False)
            return False, LOCKOUT_ERROR, ""

        if not _verify_password(password, user["password"]):
            # Increment failure counter. Lock on threshold.
            failed = int(user.get("failed_attempts", 0)) + 1
            update: dict = {"$set": {"failed_attempts": failed}}
            if failed >= MAX_FAILED_ATTEMPTS:
                update["$set"]["locked_until"] = _utcnow() + timedelta(minutes=LOCKOUT_MINUTES)
                update["$set"]["failed_attempts"] = 0
                _log_security_event("login_lockout", username, actor=username, success=False)
            users.update_one({"username": username}, update)
            _log_security_event("login", username, actor=username, success=False)
            return False, GENERIC_LOGIN_ERROR, ""

        # Successful login — clear counters and propagate forced-change flag.
        users.update_one(
            {"username": username},
            {"$unset": {"failed_attempts": "", "locked_until": ""}},
        )
        st.session_state["force_change_password"] = bool(user.get("must_change_password", False))
        role = user.get("role", "user")  # default to "user" for legacy accounts
        _log_security_event("login", username, actor=username, success=True)
        return True, user.get("display_name", username), role
    except (ConnectionFailure, ServerSelectionTimeoutError):
        return False, "Could not connect to database. Please try again later.", ""


def get_all_users() -> list[dict]:
    """Return all users (for admin user control panel)."""
    try:
        users = _get_users_collection()
        return [
            {
                "username": u["username"],
                "display_name": u.get("display_name", u["username"]),
                "role": u.get("role", "user"),
            }
            for u in users.find({}, {"password": 0})
        ]
    except (ConnectionFailure, ServerSelectionTimeoutError):
        return []


def get_security_events(
    limit: int = 200,
    event: str | None = None,
    username: str | None = None,
    only_failures: bool = False,
) -> list[dict]:
    """Return the most recent security_events records for the admin log viewer.

    Admin-only: the caller must be authenticated as an admin or super_admin.
    Non-admin callers get an empty list (defense in depth — the UI layer also
    gates the page). All filters are sanitized to strings to keep the Mongo
    query injection-safe; the $in operator we use for event types is fixed and
    not built from user input.
    """
    if not is_admin():
        return []

    # Clamp limit to a sane range.
    try:
        limit = int(limit)
    except (TypeError, ValueError):
        limit = 200
    limit = max(1, min(limit, 1000))

    query: dict = {}
    if isinstance(event, str) and event:
        query["event"] = event.strip()[:100]
    if isinstance(username, str) and username:
        query["username"] = username.strip().lower()[:100]
    if only_failures:
        query["success"] = False

    try:
        events = _get_events_collection()
        cursor = events.find(query).sort("timestamp", -1).limit(limit)
        out: list[dict] = []
        for e in cursor:
            out.append({
                "timestamp": e.get("timestamp"),
                "event": e.get("event", ""),
                "username": e.get("username", ""),
                "actor": e.get("actor", ""),
                "success": bool(e.get("success", False)),
            })
        return out
    except (ConnectionFailure, ServerSelectionTimeoutError):
        return []


def change_password(username: str, old_password: str, new_password: str) -> tuple[bool, str]:
    """Change a user's password after verifying the current password.

    Security properties:
    - Requires the current password (closes the leaked-username attack path).
    - Returns the same generic error for missing user AND wrong old password
      to prevent username enumeration.
    - Applies a 5-strike / 15-minute lockout on failed attempts, same threshold
      as login.
    - Rejects new == old, enforces the tightened password policy, and clears
      the `must_change_password` flag on success.
    - Writes a security_events audit record for every outcome.

    Note: this function does NOT consult session state — the calling UI is
    responsible for ensuring the logged-in session user matches `username`
    (see render_change_password_screen). Keeping the signature explicit makes
    the function testable without a Streamlit session.
    """
    # Guard: reject non-string inputs (prevents NoSQL operator injection)
    if not isinstance(username, str) or not isinstance(old_password, str) or not isinstance(new_password, str):
        return False, "Invalid input."
    if not old_password or not new_password:
        return False, "All fields are required."
    if old_password == new_password:
        return False, "New password must be different from the current password."

    username = username.strip().lower()[:100]
    if not username:
        return False, GENERIC_CHANGE_ERROR

    issues = _validate_password(new_password, username=username)
    if issues:
        return False, f"Password must contain: {', '.join(issues)}."

    try:
        users = _get_users_collection()
        user = users.find_one({"username": username})
        if not user:
            _log_security_event("change_password", username, actor=username, success=False)
            return False, GENERIC_CHANGE_ERROR

        if _is_locked(user, "change_locked_until"):
            _log_security_event("change_password_locked", username, actor=username, success=False)
            return False, LOCKOUT_ERROR

        if not _verify_password(old_password, user["password"]):
            failed = int(user.get("failed_change_attempts", 0)) + 1
            update: dict = {"$set": {"failed_change_attempts": failed}}
            if failed >= MAX_FAILED_ATTEMPTS:
                update["$set"]["change_locked_until"] = _utcnow() + timedelta(minutes=LOCKOUT_MINUTES)
                update["$set"]["failed_change_attempts"] = 0
                _log_security_event("change_password_lockout", username, actor=username, success=False)
            users.update_one({"username": username}, update)
            _log_security_event("change_password", username, actor=username, success=False)
            return False, GENERIC_CHANGE_ERROR

        users.update_one(
            {"username": username},
            {
                "$set": {
                    "password": _hash_password(new_password),
                    "last_password_change": _utcnow(),
                    "password_changed_by": "self",
                },
                "$unset": {
                    "failed_change_attempts": "",
                    "change_locked_until": "",
                    "must_change_password": "",
                },
            },
        )
        _log_security_event("change_password", username, actor=username, success=True)
        return True, "Password changed successfully. Please sign in again."
    except (ConnectionFailure, ServerSelectionTimeoutError):
        return False, "Could not connect to database. Please try again later."


def admin_reset_password(target_username: str, temporary_password: str) -> tuple[bool, str]:
    """Admin-initiated password reset — the only "forgot password" recovery path.

    Requires the caller to be authenticated as an admin (or super_admin). Sets
    a `must_change_password` flag on the target user so they are forced to pick
    a new password the next time they sign in. The admin delivers the temporary
    password to the user out-of-band (chat/phone/SMS) — never log or return it
    beyond the confirmation screen.
    """
    if not is_admin():
        return False, "Permission denied. Only admins can reset passwords."
    if not isinstance(target_username, str) or not isinstance(temporary_password, str):
        return False, "Invalid input."

    target_username = target_username.strip().lower()[:100]
    if not target_username:
        return False, "Target username is required."

    issues = _validate_password(temporary_password, username=target_username)
    if issues:
        return False, f"Temporary password must contain: {', '.join(issues)}."

    actor = str(st.session_state.get("username", "")).strip().lower() or "admin"
    if target_username == actor:
        return False, "Use Change Password to update your own password."

    try:
        users = _get_users_collection()
        target = users.find_one({"username": target_username})
        if not target:
            return False, "User not found."

        # Only super_admin may reset a super_admin account.
        if target.get("role") == "super_admin" and not is_super_admin():
            _log_security_event("admin_reset_password", target_username, actor=actor, success=False)
            return False, "Permission denied. Only super admins can reset super admin accounts."

        users.update_one(
            {"username": target_username},
            {
                "$set": {
                    "password": _hash_password(temporary_password),
                    "last_password_change": _utcnow(),
                    "password_changed_by": actor,
                    "must_change_password": True,
                },
                "$unset": {
                    "failed_attempts": "",
                    "locked_until": "",
                    "failed_change_attempts": "",
                    "change_locked_until": "",
                },
            },
        )
        _log_security_event("admin_reset_password", target_username, actor=actor, success=True)
        return True, (
            f"Temporary password set for '{target_username}'. "
            "Share it out-of-band; the user must change it on next sign-in."
        )
    except (ConnectionFailure, ServerSelectionTimeoutError):
        return False, "Could not connect to database. Please try again later."


def delete_user(username: str) -> tuple[bool, str]:
    """Delete a user by username."""
    try:
        users = _get_users_collection()
        result = users.delete_one({"username": username.lower()})
        if result.deleted_count == 0:
            return False, "User not found."
        return True, f"User '{username}' deleted."
    except (ConnectionFailure, ServerSelectionTimeoutError):
        return False, "Could not connect to database. Please try again later."


def update_user_role(username: str, new_role: str) -> tuple[bool, str]:
    """Promote or demote a user."""
    if new_role not in ("admin", "user"):
        return False, "Invalid role."
    try:
        users = _get_users_collection()
        result = users.update_one(
            {"username": username.lower()},
            {"$set": {"role": new_role}},
        )
        if result.matched_count == 0:
            return False, "User not found."
        return True, f"'{username}' is now a {new_role}."
    except (ConnectionFailure, ServerSelectionTimeoutError):
        return False, "Could not connect to database. Please try again later."


# ── Auth state helpers ──────────────────────────────────────────────

def is_authenticated() -> bool:
    return st.session_state.get("authenticated", False)


def is_super_admin() -> bool:
    return st.session_state.get("role", "user") == "super_admin"


def is_admin() -> bool:
    """Returns True for both admin and super_admin roles."""
    return st.session_state.get("role", "user") in ("admin", "super_admin")


# ── UI: full-page login ──────────────────────────────────────────────

def render_auth_page():
    """Full-page auth UI — Sign-In only.

    The public Change Password tab was removed. Users change their own password
    from inside the authenticated app (see render_change_password_screen), and
    users who forget their password ask an admin to issue a temporary one via
    the User Control panel.
    """
    _, col, _ = st.columns([1, 1.5, 1])

    with col:
        logo_path = Path("assets/RDB.png")
        logo_b64 = base64.b64encode(logo_path.read_bytes()).decode()
        st.markdown(f"""
        <div class="auth-card">
            <div style="display:flex;justify-content:center;margin-bottom:0.5rem;">
                <img src="data:image/png;base64,{logo_b64}" alt="RDB Logo" style="width:100px;">
            </div>
            <div class="auth-eyebrow">RDB App</div>
            <div class="auth-title">Welcome back</div>
            <div class="auth-subtitle">Enter your credentials to access your account</div>
        </div>
        """, unsafe_allow_html=True)

        with st.container(key="auth_tabs_wrapper"):
            with st.form("login_form"):
                username = st.text_input("Username", placeholder="Enter your username", key="login_user")
                password = st.text_input("Password", placeholder="••••••••", type="password", key="login_pass")
                submit = st.form_submit_button(
                    "Sign In", use_container_width=True, type="primary"
                )
                if submit:
                    if not username or not password:
                        st.error("Please fill in all fields.")
                    else:
                        ok, msg, role = authenticate_user(username, password)
                        if ok:
                            st.session_state["authenticated"] = True
                            st.session_state["username"] = msg
                            st.session_state["role"] = role
                            st.rerun()
                        else:
                            st.error(msg)

            st.caption(
                "Forgot your password? Contact an administrator — they can issue "
                "a temporary password you must change on next sign-in."
            )


def render_change_password_screen():
    """Authenticated-only Change Password screen.

    - Target is ALWAYS the logged-in user (no username input).
    - Requires the current password.
    - When `force_change_password` is set (after an admin reset), the screen
      is rendered in a mandatory mode and no other tool is reachable until a
      successful change.
    - On success, session state is cleared and the user is routed to the
      login page to sign in with the new password.
    """
    if not is_authenticated():
        st.error("You must be signed in to change your password.")
        return

    session_username = str(st.session_state.get("username", "")).strip()
    if not session_username:
        st.error("Session is missing a username. Please sign in again.")
        logout()
        return

    forced = bool(st.session_state.get("force_change_password", False))

    st.markdown(f"""
    <div class="page-hero">
        <div class="hero-eyebrow">Account</div>
        <p class="main-header">Change Password</p>
        <p class="main-subtitle">
            {"You must choose a new password before continuing." if forced
             else "Update the password for your account. You will be signed out after a successful change."}
        </p>
    </div>
    """, unsafe_allow_html=True)

    with st.form("authenticated_change_pw_form", clear_on_submit=False):
        st.caption(f"Signed in as @{session_username.lower()}")
        current_pw = st.text_input(
            "Current password" if not forced else "Temporary password",
            type="password",
            key="acp_current",
        )
        new_pw = st.text_input(
            f"New password",
            placeholder=f"Min. {MIN_PASSWORD_LENGTH} characters",
            type="password",
            key="acp_new",
        )
        confirm_pw = st.text_input(
            "Confirm new password",
            type="password",
            key="acp_confirm",
        )
        submitted = st.form_submit_button(
            "Update Password", use_container_width=True, type="primary"
        )

        if submitted:
            if not current_pw or not new_pw or not confirm_pw:
                st.error("All fields are required.")
            elif new_pw != confirm_pw:
                st.error("New passwords do not match.")
            else:
                ok, msg = change_password(session_username, current_pw, new_pw)
                if ok:
                    st.success(msg)
                    # Force a fresh sign-in with the new password.
                    logout()
                else:
                    st.error(msg)


# ── Logout ───────────────────────────────────────────────────────────

def logout():
    """Clear all session state and force a fresh page load."""
    st.session_state.clear()
    st.rerun()


# ── UI: sidebar header with logout ────────────────────────────────

def render_sidebar_header():
    """Render app name, username with role badge, and logout button."""
    username = st.session_state.get("username", "")
    role = st.session_state.get("role", "user")

    if role == "super_admin":
        role_badge = '<span class="role-badge role-super">Super Admin</span>'
    elif role == "admin":
        role_badge = '<span class="role-badge role-admin">Admin</span>'
    else:
        role_badge = '<span class="role-badge role-user">User</span>'

    with st.sidebar.container(key="sidebar_header"):
        st.logo("assets/RDB.png")
        st.markdown(
            f'<p class="sidebar-app-name">RDB App</p>'
            f'<div class="sidebar-user-row">'
            f'<span class="sidebar-username">{username}</span>'
            f'{role_badge}'
            f'</div>',
            unsafe_allow_html=True,
        )
        if st.button("Logout", key="logout_btn", icon=":material/logout:"):
            logout()
