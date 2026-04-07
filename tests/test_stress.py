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
    admin_reset_password,
    update_user_role,
    delete_user,
    get_security_events,
    MIN_PASSWORD_LENGTH,
)

# A password that satisfies the policy (≥ MIN_PASSWORD_LENGTH, not == username).
STRONG_PW = "Correcthorse99"
STRONG_PW_ALT = "Batterystaple42"


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
    with patch("auth.core._get_users_collection") as mock_get:
        c = MagicMock()
        mock_get.return_value = c
        yield c


@pytest.fixture(autouse=True)
def _silence_security_events():
    """Stub the audit logger so tests do not attempt real Mongo connections."""
    with patch("auth.core._log_security_event"):
        yield


@pytest.fixture(autouse=True)
def reset_session():
    _st_stub.session_state.clear()
    yield
    _st_stub.session_state.clear()


# ══════════════════════════════════════════════════════════════════════════════
# 1. PASSWORD VALIDATION
# ══════════════════════════════════════════════════════════════════════════════

class TestPasswordValidation:
    """Policy:
       - length >= MIN_PASSWORD_LENGTH
       - not equal to the username (when username is supplied)
    """

    def test_empty_fails(self):
        assert _validate_password("") != []

    def test_one_char_fails(self):
        assert _validate_password("a") != []

    def test_below_min_length_fails(self):
        assert _validate_password("Abc1") != []  # 4 chars
        assert _validate_password("a" * (MIN_PASSWORD_LENGTH - 1)) != []  # MIN-1

    def test_exactly_min_length_passes(self):
        pw = "a" * MIN_PASSWORD_LENGTH
        assert _validate_password(pw) == []

    def test_letters_only_passes(self):
        assert _validate_password("a" * (MIN_PASSWORD_LENGTH + 2)) == []

    def test_digits_only_passes(self):
        assert _validate_password("1" * (MIN_PASSWORD_LENGTH + 2)) == []

    def test_whitespace_only_passes_length(self):
        # Only the length rule applies — whitespace counts.
        assert _validate_password(" " * (MIN_PASSWORD_LENGTH + 4)) == []

    def test_equal_to_username_fails(self):
        name = "alice1234"
        issues = _validate_password(name, username=name)
        assert issues != []

    def test_very_long_password_passes(self):
        assert _validate_password("a" * 100) == []

    def test_special_chars_pass(self):
        assert _validate_password("!@#$%^&*") == []  # 8 chars


# ══════════════════════════════════════════════════════════════════════════════
# 2. AUTHENTICATION
# ══════════════════════════════════════════════════════════════════════════════

class TestAuthentication:

    def test_valid_login(self, col):
        with patch("auth.core._verify_password", return_value=True):
            col.find_one.return_value = _make_user("alice", "user")
            ok, name, role = authenticate_user("alice", STRONG_PW)
        assert ok is True
        assert name == "Alice"
        assert role == "user"

    def test_wrong_password(self, col):
        with patch("auth.core._verify_password", return_value=False):
            col.find_one.return_value = _make_user("alice")
            ok, msg, role = authenticate_user("alice", "wrongpass")
        assert ok is False
        assert "Invalid" in msg

    def test_unknown_user(self, col):
        col.find_one.return_value = None
        ok, msg, role = authenticate_user("ghost", STRONG_PW)
        assert ok is False
        assert "Invalid" in msg

    def test_empty_username(self, col):
        ok, msg, role = authenticate_user("", STRONG_PW)
        assert ok is False

    def test_empty_password(self, col):
        col.find_one.return_value = None
        ok, msg, role = authenticate_user("alice", "")
        assert ok is False

    def test_whitespace_username_stripped(self, col):
        with patch("auth.core._verify_password", return_value=True):
            col.find_one.return_value = _make_user("alice", "user")
            ok, _, _ = authenticate_user("  alice  ", STRONG_PW)
        # Should query "alice" not "  alice  "
        col.find_one.assert_called_with({"username": "alice"})

    def test_username_case_insensitive(self, col):
        with patch("auth.core._verify_password", return_value=True):
            col.find_one.return_value = _make_user("alice", "user")
            ok, _, _ = authenticate_user("ALICE", STRONG_PW)
        col.find_one.assert_called_with({"username": "alice"})

    def test_db_connection_failure(self, col):
        col.find_one.side_effect = ConnectionFailure("timeout")
        ok, msg, role = authenticate_user("alice", STRONG_PW)
        assert ok is False
        assert "connect" in msg.lower()

    def test_server_selection_timeout(self, col):
        col.find_one.side_effect = ServerSelectionTimeoutError("timeout")
        ok, msg, role = authenticate_user("alice", STRONG_PW)
        assert ok is False

    def test_admin_role_returned(self, col):
        with patch("auth.core._verify_password", return_value=True):
            col.find_one.return_value = _make_user("boss", "admin")
            ok, _, role = authenticate_user("boss", STRONG_PW)
        assert role == "admin"

    def test_super_admin_role_returned(self, col):
        with patch("auth.core._verify_password", return_value=True):
            col.find_one.return_value = _make_user("root", "super_admin")
            ok, _, role = authenticate_user("root", STRONG_PW)
        assert role == "super_admin"

    def test_legacy_user_defaults_to_user_role(self, col):
        with patch("auth.core._verify_password", return_value=True):
            user = _make_user("legacy")
            del user["role"]   # no role field → legacy account
            col.find_one.return_value = user
            ok, _, role = authenticate_user("legacy", STRONG_PW)
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
        ok, msg = register_user("newuser", STRONG_PW)
        assert ok is False
        assert "permission" in msg.lower()

    def test_valid_registration(self, col):
        self._as_admin()
        col.insert_one.return_value = MagicMock()
        ok, msg = register_user("newuser", STRONG_PW, "user")
        assert ok is True

    def test_username_too_short(self, col):
        self._as_admin()
        ok, msg = register_user("ab", STRONG_PW)
        assert ok is False
        assert "3" in msg

    def test_username_exactly_three_chars(self, col):
        self._as_admin()
        col.insert_one.return_value = MagicMock()
        ok, _ = register_user("abc", STRONG_PW)
        assert ok is True

    def test_password_too_short(self, col):
        self._as_admin()
        ok, msg = register_user("validuser", "Ab1")
        assert ok is False
        assert str(MIN_PASSWORD_LENGTH) in msg or "character" in msg.lower()

    def test_password_exactly_min_length(self, col):
        self._as_admin()
        col.insert_one.return_value = MagicMock()
        pw = "a" * MIN_PASSWORD_LENGTH
        ok, _ = register_user("validuser", pw)
        assert ok is True

    def test_password_letters_only_accepted(self, col):
        self._as_admin()
        col.insert_one.return_value = MagicMock()
        ok, _ = register_user("userlet", "a" * (MIN_PASSWORD_LENGTH + 2))
        assert ok is True

    def test_password_digits_only_accepted(self, col):
        self._as_admin()
        col.insert_one.return_value = MagicMock()
        ok, _ = register_user("userdig", "1" * (MIN_PASSWORD_LENGTH + 2))
        assert ok is True

    def test_password_equal_to_username_rejected(self, col):
        self._as_admin()
        # Password literally matches the (lowercased) username — must be rejected.
        name = "Alice1234"
        ok, msg = register_user(name, name.lower())
        assert ok is False

    def test_duplicate_username(self, col):
        self._as_admin()
        col.insert_one.side_effect = DuplicateKeyError("dup")
        ok, msg = register_user("existinguser", STRONG_PW)
        assert ok is False
        assert "taken" in msg.lower()

    def test_invalid_role_rejected(self, col):
        self._as_admin()
        ok, msg = register_user("user1", STRONG_PW, "superuser")
        assert ok is False

    def test_valid_roles_accepted(self, col):
        self._as_admin()
        col.insert_one.return_value = MagicMock()
        for role in ("user", "admin"):
            ok, _ = register_user(f"testuser_{role}", STRONG_PW, role)
            assert ok is True, f"role '{role}' should be accepted"

    def test_super_admin_role_requires_super_admin(self, col):
        self._as_admin()   # regular admin
        ok, msg = register_user("su1", STRONG_PW, "super_admin")
        assert ok is False
        assert "super admin" in msg.lower()

    def test_super_admin_can_create_super_admin(self, col):
        self._as_super_admin()
        col.insert_one.return_value = MagicMock()
        ok, _ = register_user("newroot", STRONG_PW, "super_admin")
        assert ok is True

    def test_username_stored_lowercase(self, col):
        self._as_admin()
        col.insert_one.return_value = MagicMock()
        register_user("MixedCase", STRONG_PW)
        call_args = col.insert_one.call_args[0][0]
        assert call_args["username"] == "mixedcase"

    def test_db_connection_failure(self, col):
        self._as_admin()
        col.insert_one.side_effect = ConnectionFailure("timeout")
        ok, msg = register_user("user1", STRONG_PW)
        assert ok is False
        assert "connect" in msg.lower()


# ══════════════════════════════════════════════════════════════════════════════
# 4. CHANGE PASSWORD
# ══════════════════════════════════════════════════════════════════════════════

class TestChangePassword:
    """Covers the hardened change_password flow (requires current password,
    lockout, audit, generic error messages, forced-change cleanup)."""

    def test_valid_change_with_correct_old_password(self, col):
        col.find_one.return_value = _make_user("alice")
        col.update_one.return_value = MagicMock(matched_count=1)
        with patch("auth.core._verify_password", return_value=True):
            ok, msg = change_password("alice", STRONG_PW, STRONG_PW_ALT)
        assert ok is True
        assert "success" in msg.lower()

    def test_wrong_old_password_returns_generic_error(self, col):
        col.find_one.return_value = _make_user("alice")
        col.update_one.return_value = MagicMock()
        with patch("auth.core._verify_password", return_value=False):
            ok, msg = change_password("alice", "WrongCurrent1", STRONG_PW_ALT)
        assert ok is False
        # Generic message — must not confirm "user exists" vs "wrong password".
        assert "invalid" in msg.lower()
        # The password field must NOT be updated on failure.
        if col.update_one.called:
            for call in col.update_one.call_args_list:
                set_doc = call[0][1].get("$set", {})
                assert "password" not in set_doc

    def test_unknown_user_returns_same_generic_error(self, col):
        col.find_one.return_value = None
        ok, msg = change_password("ghost", STRONG_PW, STRONG_PW_ALT)
        assert ok is False
        assert "invalid" in msg.lower()
        # Must not leak "user not found".
        assert "not found" not in msg.lower()

    def test_new_password_must_differ_from_old(self, col):
        ok, msg = change_password("alice", STRONG_PW, STRONG_PW)
        assert ok is False
        assert "different" in msg.lower()
        col.find_one.assert_not_called()

    def test_new_password_must_meet_policy(self, col):
        col.find_one.return_value = _make_user("alice")
        with patch("auth.core._verify_password", return_value=True):
            ok, msg = change_password("alice", STRONG_PW, "short")
        assert ok is False
        assert "character" in msg.lower() or str(MIN_PASSWORD_LENGTH) in msg

    def test_password_hashed_before_storing(self, col):
        col.find_one.return_value = _make_user("alice")
        col.update_one.return_value = MagicMock()
        with patch("auth.core._verify_password", return_value=True):
            change_password("alice", STRONG_PW, STRONG_PW_ALT)
        update_args = col.update_one.call_args[0]
        stored_pw = update_args[1]["$set"]["password"]
        assert stored_pw != STRONG_PW_ALT.encode()   # never plaintext
        assert isinstance(stored_pw, bytes)

    def test_success_records_timestamp_and_clears_forced_flag(self, col):
        col.find_one.return_value = _make_user("alice")
        col.update_one.return_value = MagicMock()
        with patch("auth.core._verify_password", return_value=True):
            change_password("alice", STRONG_PW, STRONG_PW_ALT)
        update_args = col.update_one.call_args[0]
        set_doc = update_args[1]["$set"]
        unset_doc = update_args[1].get("$unset", {})
        assert "last_password_change" in set_doc
        assert set_doc.get("password_changed_by") == "self"
        assert "must_change_password" in unset_doc
        assert "failed_change_attempts" in unset_doc
        assert "change_locked_until" in unset_doc

    def test_username_normalized_before_query(self, col):
        col.find_one.return_value = _make_user("alice")
        col.update_one.return_value = MagicMock()
        with patch("auth.core._verify_password", return_value=True):
            change_password("  ALICE  ", STRONG_PW, STRONG_PW_ALT)
        col.find_one.assert_called_with({"username": "alice"})

    def test_db_failure(self, col):
        col.find_one.side_effect = ConnectionFailure("down")
        ok, msg = change_password("alice", STRONG_PW, STRONG_PW_ALT)
        assert ok is False

    def test_lockout_after_max_failed_attempts(self, col):
        from auth.core import MAX_FAILED_ATTEMPTS
        # Start the user doc at MAX-1 failures so the next failure triggers lockout.
        user = _make_user("alice")
        user["failed_change_attempts"] = MAX_FAILED_ATTEMPTS - 1
        col.find_one.return_value = user
        with patch("auth.core._verify_password", return_value=False):
            ok, msg = change_password("alice", "WrongCurrent1", STRONG_PW_ALT)
        assert ok is False
        update_set = col.update_one.call_args[0][1]["$set"]
        assert "change_locked_until" in update_set
        assert update_set["failed_change_attempts"] == 0

    def test_locked_account_rejects_even_with_correct_old_password(self, col):
        from datetime import datetime, timedelta, timezone
        user = _make_user("alice")
        user["change_locked_until"] = datetime.now(timezone.utc) + timedelta(minutes=5)
        col.find_one.return_value = user
        with patch("auth.core._verify_password", return_value=True):
            ok, msg = change_password("alice", STRONG_PW, STRONG_PW_ALT)
        assert ok is False
        assert "locked" in msg.lower()
        # Password must NOT be updated while locked.
        if col.update_one.called:
            for call in col.update_one.call_args_list:
                set_doc = call[0][1].get("$set", {})
                assert "password" not in set_doc

    def test_nosql_injection_guards(self, col):
        ok, _ = change_password({"$ne": ""}, STRONG_PW, STRONG_PW_ALT)
        assert ok is False
        col.find_one.assert_not_called()
        ok, _ = change_password("alice", {"$ne": ""}, STRONG_PW_ALT)
        assert ok is False
        ok, _ = change_password("alice", STRONG_PW, {"$ne": ""})
        assert ok is False


# ══════════════════════════════════════════════════════════════════════════════
# 4b. ADMIN RESET PASSWORD
# ══════════════════════════════════════════════════════════════════════════════

class TestAdminResetPassword:
    """The forgot-password recovery path: admins issue a temporary password
    and the target user must change it on next sign-in."""

    def _as(self, role, username="bob"):
        _st_stub.session_state["role"] = role
        _st_stub.session_state["username"] = username

    def test_non_admin_cannot_reset(self, col):
        self._as("user")
        ok, msg = admin_reset_password("alice", STRONG_PW_ALT)
        assert ok is False
        assert "permission" in msg.lower()
        col.find_one.assert_not_called()

    def test_admin_reset_user_sets_must_change_flag(self, col):
        self._as("admin")
        col.find_one.return_value = _make_user("alice", role="user")
        col.update_one.return_value = MagicMock()
        ok, msg = admin_reset_password("alice", STRONG_PW_ALT)
        assert ok is True
        update_set = col.update_one.call_args[0][1]["$set"]
        assert update_set["must_change_password"] is True
        assert update_set["password_changed_by"] == "bob"
        assert "last_password_change" in update_set
        # Clears any prior lockout state so the user can actually sign in.
        unset_doc = col.update_one.call_args[0][1]["$unset"]
        assert "locked_until" in unset_doc
        assert "failed_attempts" in unset_doc

    def test_admin_cannot_reset_super_admin(self, col):
        self._as("admin")
        col.find_one.return_value = _make_user("root", role="super_admin")
        ok, msg = admin_reset_password("root", STRONG_PW_ALT)
        assert ok is False
        assert "super admin" in msg.lower()
        col.update_one.assert_not_called()

    def test_super_admin_can_reset_super_admin(self, col):
        self._as("super_admin", username="root1")
        col.find_one.return_value = _make_user("root2", role="super_admin")
        col.update_one.return_value = MagicMock()
        ok, _ = admin_reset_password("root2", STRONG_PW_ALT)
        assert ok is True

    def test_admin_cannot_self_reset(self, col):
        self._as("admin", username="bob")
        ok, msg = admin_reset_password("bob", STRONG_PW_ALT)
        assert ok is False
        assert "change password" in msg.lower()

    def test_temp_password_must_meet_policy(self, col):
        self._as("admin")
        ok, msg = admin_reset_password("alice", "short")
        assert ok is False
        assert "character" in msg.lower() or str(MIN_PASSWORD_LENGTH) in msg

    def test_unknown_target(self, col):
        self._as("admin")
        col.find_one.return_value = None
        ok, msg = admin_reset_password("ghost", STRONG_PW_ALT)
        assert ok is False
        assert "not found" in msg.lower()


# ══════════════════════════════════════════════════════════════════════════════
# 4c. LOGIN LOCKOUT & FORCED CHANGE PROPAGATION
# ══════════════════════════════════════════════════════════════════════════════

class TestLoginLockout:

    def test_lockout_after_max_failed_logins(self, col):
        from auth.core import MAX_FAILED_ATTEMPTS
        user = _make_user("alice")
        user["failed_attempts"] = MAX_FAILED_ATTEMPTS - 1
        col.find_one.return_value = user
        with patch("auth.core._verify_password", return_value=False):
            ok, msg, _ = authenticate_user("alice", "WrongPassword99")
        assert ok is False
        update_set = col.update_one.call_args[0][1]["$set"]
        assert "locked_until" in update_set

    def test_locked_account_cannot_login_even_with_correct_password(self, col):
        from datetime import datetime, timedelta, timezone
        user = _make_user("alice")
        user["locked_until"] = datetime.now(timezone.utc) + timedelta(minutes=5)
        col.find_one.return_value = user
        with patch("auth.core._verify_password", return_value=True):
            ok, msg, _ = authenticate_user("alice", STRONG_PW)
        assert ok is False
        assert "locked" in msg.lower()

    def test_successful_login_clears_lockout_counters(self, col):
        col.find_one.return_value = _make_user("alice")
        with patch("auth.core._verify_password", return_value=True):
            ok, _, _ = authenticate_user("alice", STRONG_PW)
        assert ok is True
        unset_doc = col.update_one.call_args[0][1]["$unset"]
        assert "failed_attempts" in unset_doc
        assert "locked_until" in unset_doc

    def test_must_change_password_flag_propagates_to_session(self, col):
        user = _make_user("alice")
        user["must_change_password"] = True
        col.find_one.return_value = user
        with patch("auth.core._verify_password", return_value=True):
            authenticate_user("alice", STRONG_PW)
        assert _st_stub.session_state.get("force_change_password") is True

    def test_normal_login_does_not_set_forced_change(self, col):
        col.find_one.return_value = _make_user("alice")
        with patch("auth.core._verify_password", return_value=True):
            authenticate_user("alice", STRONG_PW)
        assert _st_stub.session_state.get("force_change_password") is False


# ══════════════════════════════════════════════════════════════════════════════
# 4d. SECURITY LOG READER
# ══════════════════════════════════════════════════════════════════════════════

class TestGetSecurityEvents:
    """Admin-only audit log reader. Non-admins must get an empty list and must
    not trigger any DB access; admins get back a normalized list of dicts."""

    def _as(self, role):
        _st_stub.session_state["role"] = role
        _st_stub.session_state["username"] = "bob"

    def test_non_admin_gets_empty_list(self):
        self._as("user")
        with patch("auth.core._get_events_collection") as mock_get:
            result = get_security_events()
        assert result == []
        mock_get.assert_not_called()

    def test_admin_can_read_events(self):
        self._as("admin")
        from datetime import datetime, timezone
        fake_events = [
            {
                "timestamp": datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
                "event": "login",
                "username": "alice",
                "actor": "alice",
                "success": True,
            },
            {
                "timestamp": datetime(2026, 1, 1, 11, 0, 0, tzinfo=timezone.utc),
                "event": "login",
                "username": "alice",
                "actor": "alice",
                "success": False,
            },
        ]
        with patch("auth.core._get_events_collection") as mock_get:
            coll = MagicMock()
            cursor = MagicMock()
            cursor.sort.return_value = cursor
            cursor.limit.return_value = iter(fake_events)
            coll.find.return_value = cursor
            mock_get.return_value = coll
            result = get_security_events(limit=50)
        assert len(result) == 2
        assert result[0]["event"] == "login"
        assert result[0]["success"] is True
        assert result[1]["success"] is False

    def test_event_and_username_filters_are_applied_to_query(self):
        self._as("admin")
        with patch("auth.core._get_events_collection") as mock_get:
            coll = MagicMock()
            cursor = MagicMock()
            cursor.sort.return_value = cursor
            cursor.limit.return_value = iter([])
            coll.find.return_value = cursor
            mock_get.return_value = coll
            get_security_events(
                event="admin_reset_password",
                username="  ALICE  ",
                only_failures=True,
            )
            query = coll.find.call_args[0][0]
        assert query["event"] == "admin_reset_password"
        assert query["username"] == "alice"          # normalized
        assert query["success"] is False

    def test_limit_is_clamped(self):
        self._as("admin")
        with patch("auth.core._get_events_collection") as mock_get:
            coll = MagicMock()
            cursor = MagicMock()
            cursor.sort.return_value = cursor
            cursor.limit.return_value = iter([])
            coll.find.return_value = cursor
            mock_get.return_value = coll

            get_security_events(limit=99999)
            assert cursor.limit.call_args[0][0] == 1000

            get_security_events(limit=-5)
            assert cursor.limit.call_args[0][0] == 1

            get_security_events(limit="not a number")  # type: ignore[arg-type]
            assert cursor.limit.call_args[0][0] == 200

    def test_super_admin_can_read_events(self):
        self._as("super_admin")
        with patch("auth.core._get_events_collection") as mock_get:
            coll = MagicMock()
            cursor = MagicMock()
            cursor.sort.return_value = cursor
            cursor.limit.return_value = iter([])
            coll.find.return_value = cursor
            mock_get.return_value = coll
            result = get_security_events()
        assert result == []
        mock_get.assert_called_once()

    def test_db_failure_returns_empty(self):
        self._as("admin")
        with patch("auth.core._get_events_collection") as mock_get:
            mock_get.side_effect = ConnectionFailure("down")
            result = get_security_events()
        assert result == []


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
        ok, msg, role = authenticate_user({"$ne": ""}, STRONG_PW)
        assert ok is False
        col.find_one.assert_not_called()

    def test_dict_password_rejected_in_auth(self, col):
        ok, msg, role = authenticate_user("alice", {"$ne": ""})
        assert ok is False
        col.find_one.assert_not_called()

    def test_list_username_rejected_in_auth(self, col):
        ok, msg, role = authenticate_user(["admin"], STRONG_PW)
        assert ok is False

    def test_none_username_rejected_in_auth(self, col):
        ok, msg, role = authenticate_user(None, STRONG_PW)
        assert ok is False

    def test_none_password_rejected_in_auth(self, col):
        ok, msg, role = authenticate_user("alice", None)
        assert ok is False

    def test_dict_username_rejected_in_change_password(self, col):
        ok, msg = change_password({"$ne": ""}, STRONG_PW, STRONG_PW_ALT)
        assert ok is False
        col.find_one.assert_not_called()

    def test_sql_injection_string_treated_as_literal(self, col):
        # SQL injection strings must be treated as literal values, not operators
        col.find_one.return_value = None
        inject = "' OR '1'='1"
        ok, _, _ = authenticate_user(inject, STRONG_PW)
        # Must query the literal string, not bypass auth
        assert ok is False
        col.find_one.assert_called_with({"username": inject.strip().lower()})

    def test_mongo_operator_string_treated_as_literal(self, col):
        col.find_one.return_value = None
        inject = '{"$where": "sleep(5000)"}'
        ok, _, _ = authenticate_user(inject, STRONG_PW)
        assert ok is False
        col.find_one.assert_called_with({"username": inject.strip().lower()})

    def test_register_username_with_special_chars_rejected(self, col):
        _st_stub.session_state["role"] = "admin"
        # register_user has strict regex — operators can't slip through
        for bad in ['{"$ne":""}', "' OR 1=1--", "admin; DROP", "$admin", "a@b"]:
            ok, msg = register_user(bad, STRONG_PW)
            assert ok is False, f"Username '{bad}' should have been rejected"


# ══════════════════════════════════════════════════════════════════════════════
# 7. BOUNDARY / LARGE-INPUT STRESS
# ══════════════════════════════════════════════════════════════════════════════

class TestBoundaryInputs:

    def test_extremely_long_username_truncated_before_db(self, col):
        col.find_one.return_value = None
        long_username = "a" * 10_000
        authenticate_user(long_username, STRONG_PW)
        queried = col.find_one.call_args[0][0]["username"]
        assert len(queried) <= 100   # must be capped

    def test_extremely_long_password_handled(self, col):
        col.find_one.return_value = None
        ok, _, _ = authenticate_user("alice", "x" * 10_000)
        # Should not crash — DB returns None → invalid login
        assert ok is False

    def test_null_bytes_in_username(self, col):
        col.find_one.return_value = None
        ok, _, _ = authenticate_user("ali\x00ce", STRONG_PW)
        assert ok is False or col.find_one.call_args[0][0]["username"] == "ali\x00ce"

    def test_newlines_in_username_stripped(self, col):
        col.find_one.return_value = None
        authenticate_user("alice\n", STRONG_PW)
        queried = col.find_one.call_args[0][0]["username"]
        assert "\n" not in queried

    def test_unicode_username_handled(self, col):
        col.find_one.return_value = None
        ok, _, _ = authenticate_user("αλίκη", STRONG_PW)
        # Should not crash
        assert ok is False

    def test_password_validation_with_very_long_input(self):
        # Should not be slow or crash on huge input. Mix letters + digits so
        # the new policy (letter + digit + length) is satisfied.
        result = _validate_password("p1" * 50_000)
        assert result == []
