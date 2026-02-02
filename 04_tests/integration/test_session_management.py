"""
Integration tests for Session Management (P12.1.5)

Tests the session service including:
- Active session tracking
- Session listing
- Force logout (session invalidation)
- Session timeout
- Token blacklisting
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch

from services.session_service import (
    SessionService,
    Session,
    SessionError,
    create_session,
    is_session_valid,
    invalidate_session,
)


class TestSessionCreation:
    """Tests for session creation."""

    @pytest.fixture
    def session_service(self):
        """Create session service instance."""
        return SessionService()

    def test_create_session_returns_session_object(self, session_service):
        """Creating session should return Session object."""
        session = session_service.create_session(
            user_id="user123",
            access_token="token_abc",
            user_agent="Mozilla/5.0",
            ip_address="192.168.1.1"
        )

        assert isinstance(session, Session)
        assert session.user_id == "user123"
        assert session.id is not None

    def test_create_session_stores_metadata(self, session_service):
        """Session should store user agent and IP."""
        session = session_service.create_session(
            user_id="user123",
            access_token="token_abc",
            user_agent="Mozilla/5.0 Chrome",
            ip_address="10.0.0.1"
        )

        assert session.user_agent == "Mozilla/5.0 Chrome"
        assert session.ip_address == "10.0.0.1"

    def test_create_session_sets_timestamps(self, session_service):
        """Session should have created_at and last_activity."""
        before = datetime.utcnow()
        session = session_service.create_session(
            user_id="user123",
            access_token="token_abc",
            user_agent="Test",
            ip_address="127.0.0.1"
        )
        after = datetime.utcnow()

        assert before <= session.created_at <= after
        assert before <= session.last_activity <= after


class TestSessionValidation:
    """Tests for session validation."""

    @pytest.fixture
    def session_service(self):
        """Create session service instance."""
        return SessionService(session_timeout_minutes=60)

    def test_is_session_valid_active_session(self, session_service):
        """Active session should be valid."""
        session = session_service.create_session(
            user_id="user123",
            access_token="token_abc",
            user_agent="Test",
            ip_address="127.0.0.1"
        )

        assert session_service.is_session_valid(session.id) is True

    def test_is_session_valid_unknown_session(self, session_service):
        """Unknown session should be invalid."""
        assert session_service.is_session_valid("unknown-id") is False

    def test_is_session_valid_invalidated_session(self, session_service):
        """Invalidated session should be invalid."""
        session = session_service.create_session(
            user_id="user123",
            access_token="token_abc",
            user_agent="Test",
            ip_address="127.0.0.1"
        )
        session_service.invalidate_session(session.id)

        assert session_service.is_session_valid(session.id) is False

    def test_is_session_valid_expired_session(self, session_service):
        """Expired session should be invalid."""
        session = session_service.create_session(
            user_id="user123",
            access_token="token_abc",
            user_agent="Test",
            ip_address="127.0.0.1"
        )

        # Simulate time passing beyond timeout
        with patch.object(
            session_service, '_get_current_time',
            return_value=datetime.utcnow() + timedelta(minutes=61)
        ):
            assert session_service.is_session_valid(session.id) is False


class TestSessionInvalidation:
    """Tests for session invalidation (logout)."""

    @pytest.fixture
    def session_service(self):
        """Create session service instance."""
        return SessionService()

    def test_invalidate_session_marks_as_invalid(self, session_service):
        """Invalidated session should be marked invalid."""
        session = session_service.create_session(
            user_id="user123",
            access_token="token_abc",
            user_agent="Test",
            ip_address="127.0.0.1"
        )

        session_service.invalidate_session(session.id)

        updated_session = session_service.get_session(session.id)
        assert updated_session.is_valid is False
        assert updated_session.invalidated_at is not None

    def test_invalidate_session_unknown_raises_error(self, session_service):
        """Invalidating unknown session should raise error."""
        with pytest.raises(SessionError, match="Session not found"):
            session_service.invalidate_session("unknown-id")

    def test_invalidate_all_user_sessions(self, session_service):
        """Should be able to invalidate all sessions for a user."""
        # Create multiple sessions for same user
        s1 = session_service.create_session(
            user_id="user123",
            access_token="token1",
            user_agent="Chrome",
            ip_address="1.1.1.1"
        )
        s2 = session_service.create_session(
            user_id="user123",
            access_token="token2",
            user_agent="Firefox",
            ip_address="2.2.2.2"
        )
        s3 = session_service.create_session(
            user_id="other_user",
            access_token="token3",
            user_agent="Safari",
            ip_address="3.3.3.3"
        )

        # Invalidate all sessions for user123
        session_service.invalidate_all_user_sessions("user123")

        assert session_service.is_session_valid(s1.id) is False
        assert session_service.is_session_valid(s2.id) is False
        assert session_service.is_session_valid(s3.id) is True  # Other user unaffected


class TestSessionListing:
    """Tests for listing active sessions."""

    @pytest.fixture
    def session_service(self):
        """Create session service instance."""
        return SessionService()

    def test_list_user_sessions_empty(self, session_service):
        """User with no sessions should return empty list."""
        sessions = session_service.list_user_sessions("unknown_user")
        assert sessions == []

    def test_list_user_sessions_returns_all_active(self, session_service):
        """Should return all active sessions for user."""
        session_service.create_session(
            user_id="user123",
            access_token="token1",
            user_agent="Chrome",
            ip_address="1.1.1.1"
        )
        session_service.create_session(
            user_id="user123",
            access_token="token2",
            user_agent="Firefox",
            ip_address="2.2.2.2"
        )

        sessions = session_service.list_user_sessions("user123")
        assert len(sessions) == 2

    def test_list_user_sessions_excludes_invalidated(self, session_service):
        """Should not include invalidated sessions."""
        s1 = session_service.create_session(
            user_id="user123",
            access_token="token1",
            user_agent="Chrome",
            ip_address="1.1.1.1"
        )
        session_service.create_session(
            user_id="user123",
            access_token="token2",
            user_agent="Firefox",
            ip_address="2.2.2.2"
        )

        session_service.invalidate_session(s1.id)

        sessions = session_service.list_user_sessions("user123")
        assert len(sessions) == 1
        assert sessions[0].user_agent == "Firefox"


class TestTokenBlacklisting:
    """Tests for token blacklisting."""

    @pytest.fixture
    def session_service(self):
        """Create session service instance."""
        return SessionService()

    def test_blacklist_token_invalidates_session(self, session_service):
        """Blacklisting token should invalidate the session."""
        session = session_service.create_session(
            user_id="user123",
            access_token="token_abc",
            user_agent="Test",
            ip_address="127.0.0.1"
        )

        session_service.blacklist_token("token_abc")

        assert session_service.is_token_blacklisted("token_abc") is True
        assert session_service.is_session_valid(session.id) is False

    def test_is_token_blacklisted_unknown(self, session_service):
        """Unknown token should not be blacklisted."""
        assert session_service.is_token_blacklisted("unknown_token") is False

    def test_validate_token_checks_blacklist(self, session_service):
        """Token validation should check blacklist."""
        session_service.create_session(
            user_id="user123",
            access_token="token_abc",
            user_agent="Test",
            ip_address="127.0.0.1"
        )

        assert session_service.is_token_valid("token_abc") is True

        session_service.blacklist_token("token_abc")

        assert session_service.is_token_valid("token_abc") is False


class TestSessionActivity:
    """Tests for session activity tracking."""

    @pytest.fixture
    def session_service(self):
        """Create session service instance."""
        return SessionService(session_timeout_minutes=30)

    def test_touch_session_updates_last_activity(self, session_service):
        """Touching session should update last_activity."""
        session = session_service.create_session(
            user_id="user123",
            access_token="token_abc",
            user_agent="Test",
            ip_address="127.0.0.1"
        )
        original_activity = session.last_activity

        # Simulate some time passing
        with patch.object(
            session_service, '_get_current_time',
            return_value=datetime.utcnow() + timedelta(minutes=5)
        ):
            session_service.touch_session(session.id)

            updated = session_service.get_session(session.id)
            assert updated.last_activity > original_activity

    def test_touch_session_extends_validity(self, session_service):
        """Activity should extend session validity."""
        session = session_service.create_session(
            user_id="user123",
            access_token="token_abc",
            user_agent="Test",
            ip_address="127.0.0.1"
        )

        # At 29 minutes, session is still valid
        with patch.object(
            session_service, '_get_current_time',
            return_value=datetime.utcnow() + timedelta(minutes=29)
        ):
            session_service.touch_session(session.id)
            assert session_service.is_session_valid(session.id) is True

        # At 35 minutes from touch, session expired
        # But we touched at 29 minutes, so 29 + 31 = 60 minutes from start
        # Session timeout is 30 minutes from last activity
        with patch.object(
            session_service, '_get_current_time',
            return_value=datetime.utcnow() + timedelta(minutes=60)
        ):
            assert session_service.is_session_valid(session.id) is False


class TestSessionTimeout:
    """Tests for session timeout configuration."""

    def test_default_timeout_60_minutes(self):
        """Default session timeout should be 60 minutes."""
        service = SessionService()
        assert service.session_timeout_minutes == 60

    def test_custom_timeout(self):
        """Custom timeout should be configurable."""
        service = SessionService(session_timeout_minutes=120)
        assert service.session_timeout_minutes == 120

    def test_session_expires_at_timeout(self):
        """Session should expire at configured timeout."""
        service = SessionService(session_timeout_minutes=15)

        session = service.create_session(
            user_id="user123",
            access_token="token_abc",
            user_agent="Test",
            ip_address="127.0.0.1"
        )

        # At 14 minutes, still valid
        with patch.object(
            service, '_get_current_time',
            return_value=datetime.utcnow() + timedelta(minutes=14)
        ):
            assert service.is_session_valid(session.id) is True

        # At 16 minutes, expired
        with patch.object(
            service, '_get_current_time',
            return_value=datetime.utcnow() + timedelta(minutes=16)
        ):
            assert service.is_session_valid(session.id) is False
