"""
Stress & security tests for RDB App.

Covers:
  - Password validation edge cases
  - Username validation edge cases
  - Authentication (mocked DB)
  - Registration (mocked DB)
  - Change password (mocked DB)
  - NoSQL injection prevention
  - Boundary / large-input handling

Run:
    pytest tests/test_stress.py -v
"""

import sys
import types

import pytest
from unittest.mock import MagicMock, patch
from pymongo.errors import DuplicateKeyError, ConnectionFailure, ServerSelectionTimeoutError

# ── Stub streamlit BEFORE importing auth ─────────────────────────────────────
# auth.py uses st.cache_resource, st.session_state, and st.secrets at import
# time, so we mock the whole module before the import.
_st_stub = types.SimpleNamespace(
    session_state={},
    cache_resource=lambda f: f,   # pass-through: disables caching in tests
    secrets=MagicMock(),
)
_st_stub.secrets.__getitem__ = MagicMock(
    return_value={"uri": "mongodb://fake:27017", "db_name": "testdb"}
)
sys.modules["streamlit"] = _st_stub

import auth  # noqa: E402  (must come after stub)
from auth import (  # noqa: E402
    _validate_password,
    authenticate_user,
    register_user,
    change_password,
    update_user_role,
    delete_user,
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_user(username="alice", role="user", password_hash=b"$2b$hash"):
    return {
        "username": username,
        "display_name": username.capitalize(),
        "password": password_hash,
        "role": role,
    }


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def col():
    """Mock MongoDB users collection injected via patch."""
    with patch("auth._get_users_collection") as mock_get:
        c = MagicMock()
        mock_get.return_value = c
        yield c


@pytest.fixture(autouse=True)
def reset_session():
    _st_stub.session_state.clear()
    yield
    _st_stub.session_state.clear()


# ══════════════════════════════════════════════════════════════════════════════
# 1. PASSWORD VALIDATION
# ══════════════════════════════════════════════════════════════════════════════

class TestPasswordValidation:

    def test_empty_fails(self):
        assert _validate_password("") != []

    def test_one_char_fails(self):
        assert _validate_password("a") != []

    def test_seven_chars_fails(self):
        assert _validate_password("1234567") != []

    def test_exactly_eight_passes(self):
        assert _validate_password("12345678") == []

    def test_nine_chars_passes(self):
        assert _validate_password("123456789") == []

    def test_whitespace_counts_toward_length(self):
        # 8 spaces still meets the length requirement
        assert _validate_password("        ") == []

    def test_very_long_password_passes(self):
        assert _validate_password("x" * 1000) == []

    def test_unicode_password_passes_if_long_enough(self):
        assert _validate_password("αβγδεζηθ") == []  # 8 unicode chars

    def test_special_chars_pass(self):
        assert _validate_password("!@#$%^&*") == []


# ══════════════════════════════════════════════════════════════════════════════
# 2. AUTHENTICATION
# ══════════════════════════════════════════════════════════════════════════════

class TestAuthentication:

    def test_valid_login(self, col):
        with patch("auth._verify_password", return_value=True):
            col.find_one.return_value = _make_user("alice", "user")
            ok, name, role = authenticate_user("alice", "password12")
        assert ok is True
        assert name == "Alice"
        assert role == "user"

    def test_wrong_password(self, col):
        with patch("auth._verify_password", return_value=False):
            col.find_one.return_value = _make_user("alice")
            ok, msg, role = authenticate_user("alice", "wrongpass")
        assert ok is False
        assert "Invalid" in msg

    def test_unknown_user(self, col):
        col.find_one.return_value = None
        ok, msg, role = authenticate_user("ghost", "password12")
        assert ok is False
        assert "Invalid" in msg

    def test_empty_username(self, col):
        ok, msg, role = authenticate_user("", "password12")
        assert ok is False

    def test_empty_password(self, col):
        col.find_one.return_value = None
        ok, msg, role = authenticate_user("alice", "")
        assert ok is False

    def test_whitespace_username_stripped(self, col):
        with patch("auth._verify_password", return_value=True):
            col.find_one.return_value = _make_user("alice", "user")
            ok, _, _ = authenticate_user("  alice  ", "password12")
        # Should query "alice" not "  alice  "
        col.find_one.assert_called_with({"username": "alice"})

    def test_username_case_insensitive(self, col):
        with patch("auth._verify_password", return_value=True):
            col.find_one.return_value = _make_user("alice", "user")
            ok, _, _ = authenticate_user("ALICE", "password12")
        col.find_one.assert_called_with({"username": "alice"})

    def test_db_connection_failure(self, col):
        col.find_one.side_effect = ConnectionFailure("timeout")
        ok, msg, role = authenticate_user("alice", "password12")
        assert ok is False
        assert "connect" in msg.lower()

    def test_server_selection_timeout(self, col):
        col.find_one.side_effect = ServerSelectionTimeoutError("timeout")
        ok, msg, role = authenticate_user("alice", "password12")
        assert ok is False

    def test_admin_role_returned(self, col):
        with patch("auth._verify_password", return_value=True):
            col.find_one.return_value = _make_user("boss", "admin")
            ok, _, role = authenticate_user("boss", "password12")
        assert role == "admin"

    def test_super_admin_role_returned(self, col):
        with patch("auth._verify_password", return_value=True):
            col.find_one.return_value = _make_user("root", "super_admin")
            ok, _, role = authenticate_user("root", "password12")
        assert role == "super_admin"

    def test_legacy_user_defaults_to_user_role(self, col):
        with patch("auth._verify_password", return_value=True):
            user = _make_user("legacy")
            del user["role"]   # no role field → legacy account
            col.find_one.return_value = user
            ok, _, role = authenticate_user("legacy", "password12")
        assert role == "user"


# ══════════════════════════════════════════════════════════════════════════════
# 3. REGISTRATION
# ══════════════════════════════════════════════════════════════════════════════

class TestRegistration:

    def _as_admin(self):
        _st_stub.session_state["role"] = "admin"

    def _as_super_admin(self):
        _st_stub.session_state["role"] = "super_admin"

    def test_non_admin_cannot_register(self, col):
        _st_stub.session_state["role"] = "user"
        ok, msg = register_user("newuser", "password12")
        assert ok is False
        assert "permission" in msg.lower()

    def test_valid_registration(self, col):
        self._as_admin()
        col.insert_one.return_value = MagicMock()
        ok, msg = register_user("newuser", "password12", "user")
        assert ok is True

    def test_username_too_short(self, col):
        self._as_admin()
        ok, msg = register_user("ab", "password12")
        assert ok is False
        assert "3" in msg

    def test_username_exactly_three_chars(self, col):
        self._as_admin()
        col.insert_one.return_value = MagicMock()
        ok, _ = register_user("abc", "password12")
        assert ok is True

    def test_password_too_short(self, col):
        self._as_admin()
        ok, msg = register_user("validuser", "short")
        assert ok is False
        assert "8" in msg or "character" in msg.lower()

    def test_password_exactly_eight(self, col):
        self._as_admin()
        col.insert_one.return_value = MagicMock()
        ok, _ = register_user("validuser", "12345678")
        assert ok is True

    def test_duplicate_username(self, col):
        self._as_admin()
        col.insert_one.side_effect = DuplicateKeyError("dup")
        ok, msg = register_user("existinguser", "password12")
        assert ok is False
        assert "taken" in msg.lower()

    def test_invalid_role_rejected(self, col):
        self._as_admin()
        ok, msg = register_user("user1", "password12", "superuser")
        assert ok is False

    def test_valid_roles_accepted(self, col):
        self._as_admin()
        col.insert_one.return_value = MagicMock()
        for role in ("user", "admin"):
            ok, _ = register_user(f"testuser_{role}", "password12", role)
            assert ok is True, f"role '{role}' should be accepted"

    def test_super_admin_role_requires_super_admin(self, col):
        self._as_admin()   # regular admin
        ok, msg = register_user("su1", "password12", "super_admin")
        assert ok is False
        assert "super admin" in msg.lower()

    def test_super_admin_can_create_super_admin(self, col):
        self._as_super_admin()
        col.insert_one.return_value = MagicMock()
        ok, _ = register_user("newroot", "password12", "super_admin")
        assert ok is True

    def test_username_stored_lowercase(self, col):
        self._as_admin()
        col.insert_one.return_value = MagicMock()
        register_user("MixedCase", "password12")
        call_args = col.insert_one.call_args[0][0]
        assert call_args["username"] == "mixedcase"

    def test_db_connection_failure(self, col):
        self._as_admin()
        col.insert_one.side_effect = ConnectionFailure("timeout")
        ok, msg = register_user("user1", "password12")
        assert ok is False
        assert "connect" in msg.lower()


# ══════════════════════════════════════════════════════════════════════════════
# 4. CHANGE PASSWORD
# ══════════════════════════════════════════════════════════════════════════════

class TestChangePassword:

    def test_valid_change(self, col):
        col.find_one.return_value = _make_user("alice")
        col.update_one.return_value = MagicMock(matched_count=1)
        ok, msg = change_password("alice", "newpassword12")
        assert ok is True
        assert "success" in msg.lower()

    def test_password_too_short(self, col):
        ok, msg = change_password("alice", "short")
        assert ok is False
        assert "8" in msg or "character" in msg.lower()

    def test_user_not_found(self, col):
        col.find_one.return_value = None
        ok, msg = change_password("ghost", "newpassword12")
        assert ok is False
        assert "not found" in msg.lower()

    def test_password_hashed_before_storing(self, col):
        col.find_one.return_value = _make_user("alice")
        col.update_one.return_value = MagicMock()
        change_password("alice", "newpassword12")
        update_args = col.update_one.call_args[0]
        stored_pw = update_args[1]["$set"]["password"]
        assert stored_pw != b"newpassword12"   # must not be stored in plain text
        assert isinstance(stored_pw, bytes)

    def test_username_normalized_before_query(self, col):
        col.find_one.return_value = _make_user("alice")
        col.update_one.return_value = MagicMock()
        change_password("  ALICE  ", "newpassword12")
        col.find_one.assert_called_with({"username": "alice"})

    def test_db_failure(self, col):
        col.find_one.side_effect = ConnectionFailure("down")
        ok, msg = change_password("alice", "newpassword12")
        assert ok is False


# ══════════════════════════════════════════════════════════════════════════════
# 5. USER MANAGEMENT (update role / delete)
# ══════════════════════════════════════════════════════════════════════════════

class TestUserManagement:

    def test_promote_to_admin(self, col):
        col.update_one.return_value = MagicMock(matched_count=1)
        ok, msg = update_user_role("alice", "admin")
        assert ok is True
        assert "admin" in msg.lower()

    def test_demote_to_user(self, col):
        col.update_one.return_value = MagicMock(matched_count=1)
        ok, _ = update_user_role("alice", "user")
        assert ok is True

    def test_invalid_role_rejected(self, col):
        ok, msg = update_user_role("alice", "superuser")
        assert ok is False

    def test_unknown_user_role_update(self, col):
        col.update_one.return_value = MagicMock(matched_count=0)
        ok, msg = update_user_role("ghost", "admin")
        assert ok is False
        assert "not found" in msg.lower()

    def test_delete_existing_user(self, col):
        col.delete_one.return_value = MagicMock(deleted_count=1)
        ok, msg = delete_user("alice")
        assert ok is True

    def test_delete_nonexistent_user(self, col):
        col.delete_one.return_value = MagicMock(deleted_count=0)
        ok, msg = delete_user("ghost")
        assert ok is False
        assert "not found" in msg.lower()


# ══════════════════════════════════════════════════════════════════════════════
# 6. NOSQL INJECTION PREVENTION
# ══════════════════════════════════════════════════════════════════════════════

class TestNoSQLInjection:
    """
    MongoDB injection attacks pass dicts with operators like {"$ne": ""} or
    {"$gt": ""} as field values, bypassing equality checks.
    All inputs must be coerced to plain strings before reaching the DB.
    """

    def test_dict_username_rejected_in_auth(self, col):
        ok, msg, role = authenticate_user({"$ne": ""}, "password12")
        assert ok is False
        col.find_one.assert_not_called()

    def test_dict_password_rejected_in_auth(self, col):
        ok, msg, role = authenticate_user("alice", {"$ne": ""})
        assert ok is False
        col.find_one.assert_not_called()

    def test_list_username_rejected_in_auth(self, col):
        ok, msg, role = authenticate_user(["admin"], "password12")
        assert ok is False

    def test_none_username_rejected_in_auth(self, col):
        ok, msg, role = authenticate_user(None, "password12")
        assert ok is False

    def test_none_password_rejected_in_auth(self, col):
        ok, msg, role = authenticate_user("alice", None)
        assert ok is False

    def test_dict_username_rejected_in_change_password(self, col):
        ok, msg = change_password({"$ne": ""}, "newpassword12")
        assert ok is False
        col.find_one.assert_not_called()

    def test_sql_injection_string_treated_as_literal(self, col):
        # SQL injection strings must be treated as literal values, not operators
        col.find_one.return_value = None
        inject = "' OR '1'='1"
        ok, _, _ = authenticate_user(inject, "password12")
        # Must query the literal string, not bypass auth
        assert ok is False
        col.find_one.assert_called_with({"username": inject.strip().lower()})

    def test_mongo_operator_string_treated_as_literal(self, col):
        col.find_one.return_value = None
        inject = '{"$where": "sleep(5000)"}'
        ok, _, _ = authenticate_user(inject, "password12")
        assert ok is False
        col.find_one.assert_called_with({"username": inject.strip().lower()})

    def test_register_username_with_special_chars_rejected(self, col):
        _st_stub.session_state["role"] = "admin"
        # register_user has strict regex — operators can't slip through
        for bad in ['{"$ne":""}', "' OR 1=1--", "admin; DROP", "$admin", "a@b"]:
            ok, msg = register_user(bad, "password12")
            assert ok is False, f"Username '{bad}' should have been rejected"


# ══════════════════════════════════════════════════════════════════════════════
# 7. BOUNDARY / LARGE-INPUT STRESS
# ══════════════════════════════════════════════════════════════════════════════

class TestBoundaryInputs:

    def test_extremely_long_username_truncated_before_db(self, col):
        col.find_one.return_value = None
        long_username = "a" * 10_000
        authenticate_user(long_username, "password12")
        queried = col.find_one.call_args[0][0]["username"]
        assert len(queried) <= 100   # must be capped

    def test_extremely_long_password_handled(self, col):
        col.find_one.return_value = None
        ok, _, _ = authenticate_user("alice", "x" * 10_000)
        # Should not crash — DB returns None → invalid login
        assert ok is False

    def test_null_bytes_in_username(self, col):
        col.find_one.return_value = None
        ok, _, _ = authenticate_user("ali\x00ce", "password12")
        assert ok is False or col.find_one.call_args[0][0]["username"] == "ali\x00ce"

    def test_newlines_in_username_stripped(self, col):
        col.find_one.return_value = None
        authenticate_user("alice\n", "password12")
        queried = col.find_one.call_args[0][0]["username"]
        assert "\n" not in queried

    def test_unicode_username_handled(self, col):
        col.find_one.return_value = None
        ok, _, _ = authenticate_user("αλίκη", "password12")
        # Should not crash
        assert ok is False

    def test_password_validation_with_very_long_input(self):
        # Should not be slow or crash on huge input
        result = _validate_password("p" * 100_000)
        assert result == []   # length requirement met
