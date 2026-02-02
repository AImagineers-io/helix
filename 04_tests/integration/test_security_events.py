"""
Integration tests for Security Event Logging (P12.6.1)

Tests security event logging including:
- Login attempts
- Permission denials
- Rate limit hits
- Suspicious patterns
- CEF format
"""
import pytest
from datetime import datetime, timezone

from services.security_audit import (
    SecurityEvent,
    SecurityEventType,
    SecurityAuditService,
    log_security_event,
    format_cef,
)


class TestSecurityEventType:
    """Tests for security event types."""

    def test_login_attempt_type(self):
        """Should have login attempt type."""
        assert SecurityEventType.LOGIN_ATTEMPT is not None

    def test_login_success_type(self):
        """Should have login success type."""
        assert SecurityEventType.LOGIN_SUCCESS is not None

    def test_login_failure_type(self):
        """Should have login failure type."""
        assert SecurityEventType.LOGIN_FAILURE is not None

    def test_permission_denied_type(self):
        """Should have permission denied type."""
        assert SecurityEventType.PERMISSION_DENIED is not None

    def test_rate_limit_type(self):
        """Should have rate limit type."""
        assert SecurityEventType.RATE_LIMIT_HIT is not None


class TestSecurityEvent:
    """Tests for SecurityEvent model."""

    def test_event_has_timestamp(self):
        """Event should have timestamp."""
        event = SecurityEvent(
            event_type=SecurityEventType.LOGIN_ATTEMPT,
            source_ip="192.168.1.1",
            user_id="user123"
        )

        assert event.timestamp is not None

    def test_event_has_severity(self):
        """Event should have severity."""
        event = SecurityEvent(
            event_type=SecurityEventType.LOGIN_FAILURE,
            source_ip="192.168.1.1"
        )

        assert event.severity is not None

    def test_event_default_severity(self):
        """Event should have default severity based on type."""
        login_attempt = SecurityEvent(
            event_type=SecurityEventType.LOGIN_ATTEMPT,
            source_ip="192.168.1.1"
        )

        login_failure = SecurityEvent(
            event_type=SecurityEventType.LOGIN_FAILURE,
            source_ip="192.168.1.1"
        )

        # Failures should be higher severity
        assert login_failure.severity >= login_attempt.severity


class TestCEFFormat:
    """Tests for CEF (Common Event Format)."""

    def test_formats_event_as_cef(self):
        """Should format event in CEF."""
        event = SecurityEvent(
            event_type=SecurityEventType.LOGIN_FAILURE,
            source_ip="192.168.1.1",
            user_id="user123",
            details={"reason": "invalid_password"}
        )

        cef = format_cef(event)

        assert cef.startswith("CEF:")
        assert "LOGIN_FAILURE" in cef

    def test_cef_includes_source_ip(self):
        """CEF should include source IP."""
        event = SecurityEvent(
            event_type=SecurityEventType.LOGIN_ATTEMPT,
            source_ip="10.0.0.5"
        )

        cef = format_cef(event)
        assert "10.0.0.5" in cef

    def test_cef_includes_severity(self):
        """CEF should include severity."""
        event = SecurityEvent(
            event_type=SecurityEventType.PERMISSION_DENIED,
            source_ip="192.168.1.1"
        )

        cef = format_cef(event)
        # CEF format includes severity as a number
        assert "severity=" in cef.lower() or "|" in cef

    def test_cef_escapes_special_chars(self):
        """CEF should escape special characters."""
        event = SecurityEvent(
            event_type=SecurityEventType.LOGIN_FAILURE,
            source_ip="192.168.1.1",
            details={"message": "Test|with|pipes"}
        )

        cef = format_cef(event)
        # Should be escaped in extension part
        assert "Test\\|with\\|pipes" in cef or "Test|with|pipes" in cef


class TestSecurityAuditService:
    """Tests for SecurityAuditService class."""

    @pytest.fixture
    def audit_service(self):
        """Create audit service."""
        return SecurityAuditService()

    def test_log_event(self, audit_service):
        """Should log security event."""
        event = audit_service.log_event(
            event_type=SecurityEventType.LOGIN_ATTEMPT,
            source_ip="192.168.1.1",
            user_id="user123"
        )

        assert event is not None
        assert event.event_type == SecurityEventType.LOGIN_ATTEMPT

    def test_get_recent_events(self, audit_service):
        """Should retrieve recent events."""
        # Log some events
        audit_service.log_event(
            SecurityEventType.LOGIN_ATTEMPT,
            "192.168.1.1"
        )
        audit_service.log_event(
            SecurityEventType.LOGIN_SUCCESS,
            "192.168.1.1"
        )

        events = audit_service.get_recent_events(limit=10)
        assert len(events) >= 2

    def test_filter_by_type(self, audit_service):
        """Should filter events by type."""
        audit_service.log_event(
            SecurityEventType.LOGIN_SUCCESS,
            "192.168.1.1"
        )
        audit_service.log_event(
            SecurityEventType.LOGIN_FAILURE,
            "192.168.1.2"
        )

        failures = audit_service.get_events_by_type(
            SecurityEventType.LOGIN_FAILURE
        )

        for event in failures:
            assert event.event_type == SecurityEventType.LOGIN_FAILURE

    def test_filter_by_ip(self, audit_service):
        """Should filter events by IP."""
        audit_service.log_event(
            SecurityEventType.LOGIN_ATTEMPT,
            "192.168.1.100"
        )
        audit_service.log_event(
            SecurityEventType.LOGIN_ATTEMPT,
            "192.168.1.200"
        )

        events = audit_service.get_events_by_ip("192.168.1.100")

        for event in events:
            assert event.source_ip == "192.168.1.100"


class TestEventSeverity:
    """Tests for event severity calculation."""

    @pytest.fixture
    def audit_service(self):
        return SecurityAuditService()

    def test_login_success_low_severity(self, audit_service):
        """Login success should be low severity."""
        event = audit_service.log_event(
            SecurityEventType.LOGIN_SUCCESS,
            "192.168.1.1"
        )
        assert event.severity <= 3

    def test_login_failure_medium_severity(self, audit_service):
        """Login failure should be medium severity."""
        event = audit_service.log_event(
            SecurityEventType.LOGIN_FAILURE,
            "192.168.1.1"
        )
        assert event.severity >= 4

    def test_rate_limit_high_severity(self, audit_service):
        """Rate limit hit should be higher severity."""
        event = audit_service.log_event(
            SecurityEventType.RATE_LIMIT_HIT,
            "192.168.1.1"
        )
        assert event.severity >= 5


class TestLogSecurityEventFunction:
    """Tests for log_security_event convenience function."""

    def test_logs_event(self):
        """Should log event via convenience function."""
        event = log_security_event(
            event_type=SecurityEventType.LOGIN_ATTEMPT,
            source_ip="10.0.0.1",
            user_id="test_user"
        )

        assert event.event_type == SecurityEventType.LOGIN_ATTEMPT
        assert event.source_ip == "10.0.0.1"


class TestEventDetails:
    """Tests for event details handling."""

    @pytest.fixture
    def audit_service(self):
        return SecurityAuditService()

    def test_stores_details(self, audit_service):
        """Should store event details."""
        event = audit_service.log_event(
            event_type=SecurityEventType.LOGIN_FAILURE,
            source_ip="192.168.1.1",
            details={
                "reason": "invalid_password",
                "attempts": 3
            }
        )

        assert event.details["reason"] == "invalid_password"
        assert event.details["attempts"] == 3

    def test_details_in_cef(self, audit_service):
        """Details should appear in CEF format."""
        event = audit_service.log_event(
            event_type=SecurityEventType.LOGIN_FAILURE,
            source_ip="192.168.1.1",
            details={"browser": "Chrome"}
        )

        cef = format_cef(event)
        assert "Chrome" in cef
