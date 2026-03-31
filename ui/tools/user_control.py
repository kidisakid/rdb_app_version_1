"""
User Control tool — Admin-only panel for managing users.

Role rules:
  - admin and super_admin can promote users → admin and demote admins → user
  - super_admin rows are protected (no actions allowed on them)
  - Only super_admin can create super_admin accounts
"""

import streamlit as st
from auth import register_user, delete_user, update_user_role, get_all_users, is_super_admin

_BADGE = {
    "super_admin": ("role-super", "Super Admin"),
    "admin":       ("role-admin", "Admin"),
    "user":        ("role-user",  "User"),
}


def tool_user_control():
    st.markdown("""
    <div class="page-hero">
        <div class="hero-eyebrow">Admin Panel</div>
        <p class="main-header">User Control</p>
        <p class="main-subtitle">Manage who has access to the RDB App — add, remove, or change user roles.</p>
        <div class="hero-actions">
            <span class="hero-badge"><span class="hero-badge-dot"></span>Admin only</span>
            <span class="hero-badge">Add users</span>
            <span class="hero-badge">Manage roles</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    current_user = st.session_state.get("username", "").lower()
    current_role = st.session_state.get("role", "user")

    # ── User list ────────────────────────────────────────────────────
    st.markdown(
        '<div class="section-divider">'
        '<span class="section-divider-label">All Users</span>'
        '<span class="section-divider-line"></span></div>',
        unsafe_allow_html=True,
    )

    users = get_all_users()

    if not users:
        st.info("No users found or could not connect to database.")
    else:
        h_name, h_role, h_action, h_delete = st.columns([5, 2, 1, 1])
        h_name.markdown('<div class="uc-header">User</div>', unsafe_allow_html=True)
        h_role.markdown('<div class="uc-header">Role</div>', unsafe_allow_html=True)
        st.markdown('<div class="uc-divider"></div>', unsafe_allow_html=True)

        for user in users:
            uname    = user["username"]
            display  = user["display_name"]
            role     = user["role"]
            is_self  = uname == current_user

            # Protected: super_admin rows can never be acted on
            # Admins and super_admins can act on everyone else (except themselves)
            can_act = (
                not is_self
                and role != "super_admin"
                and current_role in ("admin", "super_admin")
            )

            col_name, col_role, col_action, col_delete = st.columns(
                [5, 2, 1, 1], vertical_alignment="center"
            )

            with col_name:
                you = "&thinsp;<span class='uc-you'>you</span>" if is_self else ""
                st.markdown(
                    f'<span class="uc-username">{display}{you}</span>'
                    f'<span class="uc-handle"> @{uname}</span>',
                    unsafe_allow_html=True,
                )

            with col_role:
                badge_cls, badge_label = _BADGE.get(role, ("role-user", role.capitalize()))
                st.markdown(
                    f'<span class="role-badge {badge_cls}">{badge_label}</span>',
                    unsafe_allow_html=True,
                )

            with col_action:
                if can_act:
                    if role == "user":
                        if st.button(
                            "",
                            key=f"promote_{uname}",
                            icon=":material/arrow_upward:",
                            help=f"Promote {display} to Admin",
                        ):
                            ok, msg = update_user_role(uname, "admin")
                            st.toast(msg, icon="✅" if ok else "❌")
                            st.rerun()
                    elif role == "admin":
                        if st.button(
                            "",
                            key=f"demote_{uname}",
                            icon=":material/arrow_downward:",
                            help=f"Demote {display} to User",
                        ):
                            ok, msg = update_user_role(uname, "user")
                            st.toast(msg, icon="✅" if ok else "❌")
                            st.rerun()

            with col_delete:
                if can_act:
                    if st.button(
                        "",
                        key=f"delete_{uname}",
                        icon=":material/delete:",
                        help=f"Delete {display}",
                    ):
                        ok, msg = delete_user(uname)
                        st.toast(msg, icon="✅" if ok else "❌")
                        st.rerun()

    # ── Add new user ─────────────────────────────────────────────────
    st.markdown(
        '<div class="section-divider" style="margin-top:1.5rem">'
        '<span class="section-divider-label">Add New User</span>'
        '<span class="section-divider-line"></span></div>',
        unsafe_allow_html=True,
    )

    role_options = ["user", "admin"]
    if is_super_admin():
        role_options.append("super_admin")

    with st.form("add_user_form", clear_on_submit=True):
        col_u, col_p = st.columns(2)
        with col_u:
            new_username = st.text_input("Username")
        with col_p:
            new_password = st.text_input("Password", type="password")
        st.caption("Minimum 8 characters")

        col_r, col_b = st.columns([2, 1], vertical_alignment="bottom")
        with col_r:
            new_role = st.selectbox("Role", role_options)
        with col_b:
            submitted = st.form_submit_button(
                "Add User", use_container_width=True, type="primary"
            )

        if submitted:
            if not new_username or not new_password:
                st.error("Username and password are required.")
            else:
                ok, msg = register_user(new_username, new_password, role=new_role)
                if ok:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)
