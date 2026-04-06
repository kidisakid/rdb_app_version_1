"""
Authentication module — MongoDB-backed login with role-based access control.
Roles: "admin" (all tools + user management) | "user" (pipeline + merge only)
"""

import re

import bcrypt
import streamlit as st
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, DuplicateKeyError, ServerSelectionTimeoutError


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


# ── Password helpers ────────────────────────────────────────────────

def _hash_password(password: str) -> bytes:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())


def _verify_password(password: str, hashed: bytes) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), hashed)


def _validate_password(password: str) -> list[str]:
    """Returns a list of unmet password requirements."""
    if len(password) < 8:
        return ["at least 8 characters"]
    return []


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
    issues = _validate_password(password)
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
    """Authenticate a user. Returns (success, display_name | error, role)."""
    # Guard: reject non-string inputs (prevents NoSQL operator injection)
    if not isinstance(username, str) or not isinstance(password, str):
        return False, "Invalid input.", ""
    username = username.strip().lower()[:100]
    if not username:
        return False, "Invalid username or password.", ""
    try:
        users = _get_users_collection()
        user = users.find_one({"username": username})
        if not user:
            return False, "Invalid username or password.", ""
        if not _verify_password(password, user["password"]):
            return False, "Invalid username or password.", ""
        role = user.get("role", "user")  # default to "user" for legacy accounts
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


def change_password(username: str, new_password: str) -> tuple[bool, str]:
    """Change a user's password by username."""
    if not isinstance(username, str) or not isinstance(new_password, str):
        return False, "Invalid input."
    issues = _validate_password(new_password)
    if issues:
        return False, f"Password must contain: {', '.join(issues)}."
    username = username.strip().lower()[:100]
    try:
        users = _get_users_collection()
        user = users.find_one({"username": username})
        if not user:
            return False, "User not found."
        users.update_one(
            {"username": username},
            {"$set": {"password": _hash_password(new_password)}},
        )
        return True, "Password changed successfully."
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
    """Full-page auth UI — Sign In and Change Password tabs."""
    _, col, _ = st.columns([1, 1.5, 1])

    with col:
        st.markdown("""
        <div class="auth-card">
            <div class="auth-logo">RDB</div>
            <div class="auth-eyebrow">RDB App</div>
            <div class="auth-title">Welcome back</div>
            <div class="auth-subtitle">Enter your credentials to access your account</div>
        </div>
        """, unsafe_allow_html=True)

        with st.container(key="auth_tabs_wrapper"):
            login_tab, change_pw_tab = st.tabs(["Sign In", "Change Password"])

            with login_tab:
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

            with change_pw_tab:
                with st.form("change_pw_form", clear_on_submit=True):
                    cp_username   = st.text_input("Username", placeholder="Enter your username", key="cp_user")
                    cp_new_pw     = st.text_input("New password", placeholder="Min. 8 characters", type="password", key="cp_new")
                    st.caption("Minimum 8 characters")
                    cp_confirm_pw = st.text_input("Confirm new password", placeholder="Re-enter new password", type="password", key="cp_confirm")
                    cp_submit     = st.form_submit_button(
                        "Update Password", use_container_width=True, type="primary"
                    )
                    if cp_submit:
                        if not cp_username or not cp_new_pw or not cp_confirm_pw:
                            st.error("All fields are required.")
                        elif cp_new_pw != cp_confirm_pw:
                            st.error("New passwords do not match.")
                        else:
                            ok, msg = change_password(cp_username.strip().lower(), cp_new_pw)
                            if ok:
                                st.success(msg)
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
