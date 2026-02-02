"""
Security Audit Service for security event logging.

Provides:
- Security event logging
- Event types and severity
- CEF (Common Event Format) output
- Event querying and filtering

Event types:
- LOGIN_ATTEMPT, LOGIN_SUCCESS, LOGIN_FAILURE
- PERMISSION_DENIED
- RATE_LIMIT_HIT
- SUSPICIOUS_ACTIVITY
- API_KEY_ROTATION
- SESSION_INVALIDATED
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional


class SecurityEventType(Enum):
    """Types of security events."""
    LOGIN_ATTEMPT = "login_attempt"
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILURE = "login_failure"
    PERMISSION_DENIED = "permission_denied"
    RATE_LIMIT_HIT = "rate_limit_hit"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    API_KEY_ROTATION = "api_key_rotation"
    SESSION_INVALIDATED = "session_invalidated"
    INJECTION_ATTEMPT = "injection_attempt"
    MFA_FAILURE = "mfa_failure"


# Default severity levels (1-10 scale)
DEFAULT_SEVERITY = {
    SecurityEventType.LOGIN_ATTEMPT: 1,
    SecurityEventType.LOGIN_SUCCESS: 2,
    SecurityEventType.LOGIN_FAILURE: 5,
    SecurityEventType.PERMISSION_DENIED: 6,
    SecurityEventType.RATE_LIMIT_HIT: 7,
    SecurityEventType.SUSPICIOUS_ACTIVITY: 8,
    SecurityEventType.API_KEY_ROTATION: 3,
    SecurityEventType.SESSION_INVALIDATED: 4,
    SecurityEventType.INJECTION_ATTEMPT: 9,
    SecurityEventType.MFA_FAILURE: 6,
}


@dataclass
class SecurityEvent:
    """A security event for audit logging."""
    event_type: SecurityEventType
    source_ip: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    details: dict[str, Any] = field(default_factory=dict)
    severity: int = 0

    def __post_init__(self):
        """Set default severity based on event type."""
        if self.severity == 0:
            self.severity = DEFAULT_SEVERITY.get(self.event_type, 5)


def _escape_cef_value(value: str) -> str:
    """
    Escape special characters for CEF format.

    Args:
        value: Value to escape

    Returns:
        str: Escaped value
    """
    if not value:
        return ""

    # Escape backslash first
    value = value.replace("\\", "\\\\")
    # Escape pipe
    value = value.replace("|", "\\|")
    # Escape equals
    value = value.replace("=", "\\=")

    return value


def format_cef(event: SecurityEvent) -> str:
    """
    Format security event in CEF (Common Event Format).

    CEF format:
    CEF:Version|Device Vendor|Device Product|Device Version|Signature ID|Name|Severity|Extension

    Args:
        event: Security event to format

    Returns:
        str: CEF formatted string
    """
    # CEF header fields
    version = "0"
    vendor = "Helix"
    product = "SecurityAudit"
    device_version = "1.0"
    signature_id = event.event_type.value
    name = event.event_type.name
    severity = str(event.severity)

    # Build extension key-value pairs
    extensions = [
        f"src={event.source_ip}",
        f"rt={int(event.timestamp.timestamp() * 1000)}",  # milliseconds
    ]

    if event.user_id:
        extensions.append(f"duser={_escape_cef_value(event.user_id)}")

    if event.session_id:
        extensions.append(f"cs1={_escape_cef_value(event.session_id)}")
        extensions.append("cs1Label=sessionId")

    # Add details
    for key, value in event.details.items():
        safe_key = key.replace(" ", "_")[:23]  # CEF key limit
        safe_value = _escape_cef_value(str(value))
        extensions.append(f"cs2={safe_value}")
        extensions.append(f"cs2Label={safe_key}")

    # Add severity as extension too for searchability
    extensions.append(f"severity={severity}")

    extension_str = " ".join(extensions)

    return f"CEF:{version}|{vendor}|{product}|{device_version}|{signature_id}|{name}|{severity}|{extension_str}"


class SecurityAuditService:
    """
    Service for logging and querying security events.

    Stores events in memory (for now) and provides
    filtering and CEF formatting.
    """

    def __init__(self):
        """Initialize security audit service."""
        self._events: list[SecurityEvent] = []

    def log_event(
        self,
        event_type: SecurityEventType,
        source_ip: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        details: Optional[dict] = None
    ) -> SecurityEvent:
        """
        Log a security event.

        Args:
            event_type: Type of event
            source_ip: Source IP address
            user_id: User ID if known
            session_id: Session ID if applicable
            details: Additional event details

        Returns:
            SecurityEvent: Logged event
        """
        event = SecurityEvent(
            event_type=event_type,
            source_ip=source_ip,
            user_id=user_id,
            session_id=session_id,
            details=details or {}
        )

        self._events.append(event)

        return event

    def get_recent_events(self, limit: int = 100) -> list[SecurityEvent]:
        """
        Get recent security events.

        Args:
            limit: Maximum events to return

        Returns:
            list[SecurityEvent]: Recent events
        """
        return sorted(
            self._events,
            key=lambda e: e.timestamp,
            reverse=True
        )[:limit]

    def get_events_by_type(
        self,
        event_type: SecurityEventType
    ) -> list[SecurityEvent]:
        """
        Get events of a specific type.

        Args:
            event_type: Type to filter by

        Returns:
            list[SecurityEvent]: Matching events
        """
        return [e for e in self._events if e.event_type == event_type]

    def get_events_by_ip(self, source_ip: str) -> list[SecurityEvent]:
        """
        Get events from a specific IP.

        Args:
            source_ip: IP address to filter by

        Returns:
            list[SecurityEvent]: Matching events
        """
        return [e for e in self._events if e.source_ip == source_ip]

    def get_events_by_user(self, user_id: str) -> list[SecurityEvent]:
        """
        Get events for a specific user.

        Args:
            user_id: User ID to filter by

        Returns:
            list[SecurityEvent]: Matching events
        """
        return [e for e in self._events if e.user_id == user_id]

    def get_high_severity_events(
        self,
        min_severity: int = 7
    ) -> list[SecurityEvent]:
        """
        Get high severity events.

        Args:
            min_severity: Minimum severity level

        Returns:
            list[SecurityEvent]: High severity events
        """
        return [e for e in self._events if e.severity >= min_severity]

    def clear_events(self) -> None:
        """Clear all events (for testing)."""
        self._events.clear()


# Global audit service instance
_audit_service: Optional[SecurityAuditService] = None


def _get_audit_service() -> SecurityAuditService:
    """Get or create global audit service."""
    global _audit_service

    if _audit_service is None:
        _audit_service = SecurityAuditService()

    return _audit_service


def log_security_event(
    event_type: SecurityEventType,
    source_ip: str,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    details: Optional[dict] = None
) -> SecurityEvent:
    """
    Convenience function to log security event.

    Args:
        event_type: Type of event
        source_ip: Source IP address
        user_id: User ID if known
        session_id: Session ID if applicable
        details: Additional details

    Returns:
        SecurityEvent: Logged event
    """
    return _get_audit_service().log_event(
        event_type=event_type,
        source_ip=source_ip,
        user_id=user_id,
        session_id=session_id,
        details=details
    )
