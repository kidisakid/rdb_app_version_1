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
    st.markdown('<div class="uc-page-wrap"></div>', unsafe_allow_html=True)
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

    try:
        users = get_all_users()
    except Exception as e:
        st.error(f"Failed to load users: {e}")
        users = []

    if not users:
        st.info("No users found or could not connect to database.")
    else:
        for user in users:
            uname    = user["username"]
            display  = user["display_name"]
            role     = user["role"]
            is_self  = uname == current_user

            can_act = (
                not is_self
                and role != "super_admin"
                and current_role in ("admin", "super_admin")
            )

            badge_cls, badge_label = _BADGE.get(role, ("role-user", role.capitalize()))
            you = "&thinsp;<span class='uc-you'>you</span>" if is_self else ""

            # Determine how many action buttons this row needs
            n_buttons = 0
            if can_act:
                n_buttons = 2 if role in ("user", "admin") else 1  # role btn + delete

            if n_buttons:
                col_info, col_actions = st.columns([3, 1], vertical_alignment="center")
            else:
                col_info, col_actions = st.columns([1, 0.001], vertical_alignment="center")

            with col_info:
                st.markdown(
                    f'<div class="uc-row-info">'
                    f'<span class="uc-username">{display}{you}</span>'
                    f'<span class="uc-handle"> @{uname}</span>'
                    f'&ensp;<span class="role-badge {badge_cls}">{badge_label}</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

            with col_actions:
                if can_act:
                    btn_cols = st.columns(n_buttons)
                    col_idx = 0
                    if role == "user":
                        with btn_cols[col_idx]:
                            if st.button(
                                "",
                                key=f"promote_{uname}",
                                icon=":material/arrow_upward:",
                                help=f"Promote {display} to Admin",
                                use_container_width=True,
                            ):
                                ok, msg = update_user_role(uname, "admin")
                                st.toast(msg, icon="✅" if ok else "❌")
                                st.rerun()
                        col_idx += 1
                    elif role == "admin":
                        with btn_cols[col_idx]:
                            if st.button(
                                "",
                                key=f"demote_{uname}",
                                icon=":material/arrow_downward:",
                                help=f"Demote {display} to User",
                                use_container_width=True,
                            ):
                                ok, msg = update_user_role(uname, "user")
                                st.toast(msg, icon="✅" if ok else "❌")
                                st.rerun()
                        col_idx += 1
                    with btn_cols[col_idx]:
                        if st.button(
                            "",
                            key=f"delete_{uname}",
                            icon=":material/delete:",
                            help=f"Delete {display}",
                            use_container_width=True,
                        ):
                            st.session_state["confirm_delete_user"] = uname

            if st.session_state.get("confirm_delete_user") == uname:
                st.warning(f"Are you sure you want to delete **{display}** (@{uname})? This cannot be undone.")
                c_yes, c_no = st.columns(2)
                with c_yes:
                    if st.button("Confirm", key=f"confirm_yes_{uname}", type="primary", use_container_width=True):
                        try:
                            ok, msg = delete_user(uname)
                            st.toast(msg, icon="✅" if ok else "❌")
                        except Exception as e:
                            st.error(f"Failed to delete user: {e}")
                        st.session_state.pop("confirm_delete_user", None)
                        st.rerun()
                with c_no:
                    if st.button("Cancel", key=f"confirm_no_{uname}", use_container_width=True):
                        st.session_state.pop("confirm_delete_user", None)
                        st.rerun()

            st.markdown('<div class="uc-divider"></div>', unsafe_allow_html=True)

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
                try:
                    ok, msg = register_user(new_username, new_password, role=new_role)
                    if ok:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)
                except Exception as e:
                    st.error(f"Failed to register user: {e}")
