"""
Authentication module — MongoDB-backed login and registration.
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
    client = MongoClient(uri, serverSelectionTimeoutMS=5000)
    client.admin.command("ping")

    # Ensure unique index on username (idempotent)
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


# ── User operations ─────────────────────────────────────────────────

def register_user(username: str, password: str) -> tuple[bool, str]:
    """Register a new user. Returns (success, message)."""
    username = username.strip()
    if len(username) < 3:
        return False, "Username must be at least 3 characters."
    if len(password) < 6:
        return False, "Password must be at least 6 characters."
    if not re.match(r"^[a-zA-Z0-9_]+$", username):
        return False, "Username can only contain letters, numbers, and underscores."

    try:
        users = _get_users_collection()
        users.insert_one({
            "username": username.lower(),
            "display_name": username,
            "password": _hash_password(password),
        })
        return True, "Account created successfully."
    except DuplicateKeyError:
        return False, "Username already taken."
    except (ConnectionFailure, ServerSelectionTimeoutError):
        return False, "Could not connect to database. Please try again later."


def authenticate_user(username: str, password: str) -> tuple[bool, str]:
    """Authenticate a user. Returns (success, display_name | error message)."""
    try:
        users = _get_users_collection()
        user = users.find_one({"username": username.strip().lower()})
        if not user:
            return False, "Invalid username or password."
        if not _verify_password(password, user["password"]):
            return False, "Invalid username or password."
        return True, user.get("display_name", username)
    except (ConnectionFailure, ServerSelectionTimeoutError):
        return False, "Could not connect to database. Please try again later."


# ── Auth state helpers ──────────────────────────────────────────────

def is_authenticated() -> bool:
    return st.session_state.get("authenticated", False)


# ── UI: full-page login / registration ──────────────────────────────

def render_auth_page():
    """Full-page auth UI with Sign In and Create Account tabs."""
    _, col, _ = st.columns([1, 1.5, 1])

    with col:
        st.markdown(
            '<p style="font-family: \'DM Serif Display\', Georgia, serif; '
            'font-size: 2rem; text-align: center; margin-bottom: 0.2rem;">'
            "RDB App</p>",
            unsafe_allow_html=True,
        )
        st.markdown(
            '<p style="font-family: \'DM Sans\', sans-serif; font-size: 0.9rem; '
            'color: #64748b; text-align: center; margin-bottom: 1.5rem;">'
            "Sign in to continue</p>",
            unsafe_allow_html=True,
        )

        login_tab, register_tab = st.tabs(["Sign In", "Create Account"])

        with login_tab:
            with st.form("login_form"):
                username = st.text_input("Username", key="login_user")
                password = st.text_input("Password", type="password", key="login_pass")
                submit = st.form_submit_button(
                    "Sign In", use_container_width=True, type="primary"
                )
                if submit:
                    if not username or not password:
                        st.error("Please fill in all fields.")
                    else:
                        ok, msg = authenticate_user(username, password)
                        if ok:
                            st.session_state["authenticated"] = True
                            st.session_state["username"] = msg
                            st.rerun()
                        else:
                            st.error(msg)

        with register_tab:
            with st.form("register_form"):
                new_user = st.text_input("Username", key="reg_user")
                new_pass = st.text_input("Password", type="password", key="reg_pass")
                confirm_pass = st.text_input(
                    "Confirm password", type="password", key="reg_confirm"
                )
                register = st.form_submit_button(
                    "Create Account", use_container_width=True, type="primary"
                )
                if register:
                    if not new_user or not new_pass or not confirm_pass:
                        st.error("Please fill in all fields.")
                    elif new_pass != confirm_pass:
                        st.error("Passwords do not match.")
                    else:
                        ok, msg = register_user(new_user, new_pass)
                        if ok:
                            st.success(msg + " You can now sign in.")
                        else:
                            st.error(msg)


# ── Logout ───────────────────────────────────────────────────────────

def logout():
    """Clear all session state and force a fresh page load."""
    st.session_state.clear()
    st.rerun()


# ── UI: sidebar header with logout ────────────────────────────────

def render_sidebar_header():
    """Render app name, username, and logout in one sidebar row."""
    username = st.session_state.get("username", "")

    with st.sidebar.container(key="sidebar_header"):
        st.markdown(
            f'<p class="sidebar-app-name">RDB App</p>'
            f'<p class="sidebar-username">{username}</p>',
            unsafe_allow_html=True,
        )
        if st.button("Logout", key="logout_btn", icon=":material/logout:"):
            logout()
