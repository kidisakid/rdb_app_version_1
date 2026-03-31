"""Auth package — re-exports everything from core so imports never need to change."""
from auth.core import (
    authenticate_user,
    register_user,
    change_password,
    delete_user,
    update_user_role,
    get_all_users,
    is_authenticated,
    is_admin,
    is_super_admin,
    logout,
    render_auth_page,
    render_sidebar_header,
    _validate_password,
)

__all__ = [
    "authenticate_user",
    "register_user",
    "change_password",
    "delete_user",
    "update_user_role",
    "get_all_users",
    "is_authenticated",
    "is_admin",
    "is_super_admin",
    "logout",
    "render_auth_page",
    "render_sidebar_header",
    "_validate_password",
]
