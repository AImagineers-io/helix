"""
Session Management Service for tracking and managing user sessions.

Provides:
- Active session tracking with metadata
- Session listing for users
- Force logout (session invalidation)
- Session timeout with activity-based extension
- Token blacklisting for immediate invalidation

This service enables:
- Users to see their active sessions across devices
- Admins to force logout specific sessions
- Security measures like session timeout
- Immediate token invalidation on logout
"""
import secrets
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional

# Session configuration
DEFAULT_SESSION_TIMEOUT_MINUTES = 60


class SessionError(Exception):
    """Raised when session operations fail."""
    pass


@dataclass
class Session:
    """
    Represents an active user session.

    Attributes:
        id: Unique session identifier
        user_id: User who owns this session
        access_token: JWT access token for this session
        user_agent: Browser/client user agent string
        ip_address: Client IP address
        created_at: When session was created
        last_activity: Last activity timestamp (for timeout)
        is_valid: Whether session is currently valid
        invalidated_at: When session was invalidated (if applicable)
    """
    id: str
    user_id: str
    access_token: str
    user_agent: str
    ip_address: str
    created_at: datetime
    last_activity: datetime
    is_valid: bool = True
    invalidated_at: Optional[datetime] = None

    @property
    def is_active(self) -> bool:
        """Alias for is_valid for clearer semantics."""
        return self.is_valid

    def get_device_info(self) -> str:
        """Get formatted device info for display."""
        # Extract browser name from user agent
        ua = self.user_agent.lower()
        if "chrome" in ua:
            browser = "Chrome"
        elif "firefox" in ua:
            browser = "Firefox"
        elif "safari" in ua:
            browser = "Safari"
        elif "edge" in ua:
            browser = "Edge"
        else:
            browser = "Unknown Browser"
        return f"{browser} from {self.ip_address}"


def create_session(
    user_id: str,
    access_token: str,
    user_agent: str,
    ip_address: str
) -> Session:
    """
    Create a new session.

    Args:
        user_id: User identifier
        access_token: JWT access token
        user_agent: Client user agent
        ip_address: Client IP address

    Returns:
        Session: New session object
    """
    now = datetime.utcnow()
    return Session(
        id=secrets.token_hex(16),
        user_id=user_id,
        access_token=access_token,
        user_agent=user_agent,
        ip_address=ip_address,
        created_at=now,
        last_activity=now,
    )


def is_session_valid(session: Session, timeout_minutes: int, current_time: datetime) -> bool:
    """
    Check if a session is valid.

    Args:
        session: Session to check
        timeout_minutes: Session timeout in minutes
        current_time: Current time for comparison

    Returns:
        bool: True if session is valid
    """
    if not session.is_valid:
        return False

    timeout_threshold = session.last_activity + timedelta(minutes=timeout_minutes)
    return current_time < timeout_threshold


def invalidate_session(session: Session, current_time: datetime) -> None:
    """
    Invalidate a session.

    Args:
        session: Session to invalidate
        current_time: Time of invalidation
    """
    session.is_valid = False
    session.invalidated_at = current_time


class SessionService:
    """
    Service for managing user sessions.

    Features:
    - Track active sessions per user
    - Session timeout with activity refresh
    - Force logout (single or all sessions)
    - Token blacklisting

    Attributes:
        session_timeout_minutes: Minutes of inactivity before timeout
    """

    def __init__(self, session_timeout_minutes: int = DEFAULT_SESSION_TIMEOUT_MINUTES):
        """
        Initialize session service.

        Args:
            session_timeout_minutes: Session timeout in minutes (default 60)
        """
        self.session_timeout_minutes = session_timeout_minutes
        self._sessions: dict[str, Session] = {}  # session_id -> Session
        self._token_to_session: dict[str, str] = {}  # access_token -> session_id
        self._blacklisted_tokens: set[str] = set()

    def _get_current_time(self) -> datetime:
        """Get current UTC time. Extracted for testing."""
        return datetime.utcnow()

    def create_session(
        self,
        user_id: str,
        access_token: str,
        user_agent: str,
        ip_address: str
    ) -> Session:
        """
        Create and store a new session.

        Args:
            user_id: User identifier
            access_token: JWT access token
            user_agent: Client user agent string
            ip_address: Client IP address

        Returns:
            Session: New session object
        """
        session = create_session(
            user_id=user_id,
            access_token=access_token,
            user_agent=user_agent,
            ip_address=ip_address,
        )
        # Override timestamps with service time
        now = self._get_current_time()
        session.created_at = now
        session.last_activity = now

        self._sessions[session.id] = session
        self._token_to_session[access_token] = session.id

        return session

    def get_session(self, session_id: str) -> Optional[Session]:
        """
        Get session by ID.

        Args:
            session_id: Session identifier

        Returns:
            Session or None if not found
        """
        return self._sessions.get(session_id)

    def is_session_valid(self, session_id: str) -> bool:
        """
        Check if a session is currently valid.

        A session is invalid if:
        - It doesn't exist
        - It has been invalidated
        - It has timed out
        - Its token is blacklisted

        Args:
            session_id: Session identifier

        Returns:
            bool: True if session is valid
        """
        session = self._sessions.get(session_id)
        if session is None:
            return False

        # Check if token is blacklisted
        if session.access_token in self._blacklisted_tokens:
            return False

        return is_session_valid(
            session=session,
            timeout_minutes=self.session_timeout_minutes,
            current_time=self._get_current_time()
        )

    def invalidate_session(self, session_id: str) -> None:
        """
        Invalidate a specific session (force logout).

        Args:
            session_id: Session to invalidate

        Raises:
            SessionError: If session not found
        """
        session = self._sessions.get(session_id)
        if session is None:
            raise SessionError("Session not found")

        invalidate_session(session, self._get_current_time())
        # Also blacklist the token
        self._blacklisted_tokens.add(session.access_token)

    def invalidate_all_user_sessions(self, user_id: str) -> int:
        """
        Invalidate all sessions for a user (force logout everywhere).

        Args:
            user_id: User identifier

        Returns:
            int: Number of sessions invalidated
        """
        count = 0
        current_time = self._get_current_time()

        for session in self._sessions.values():
            if session.user_id == user_id and session.is_valid:
                invalidate_session(session, current_time)
                self._blacklisted_tokens.add(session.access_token)
                count += 1

        return count

    def list_user_sessions(self, user_id: str) -> list[Session]:
        """
        List all active sessions for a user.

        Args:
            user_id: User identifier

        Returns:
            List of active Session objects
        """
        sessions = []
        current_time = self._get_current_time()

        for session in self._sessions.values():
            if session.user_id != user_id:
                continue
            if not is_session_valid(session, self.session_timeout_minutes, current_time):
                continue
            if session.access_token in self._blacklisted_tokens:
                continue
            sessions.append(session)

        return sessions

    def touch_session(self, session_id: str) -> None:
        """
        Update session last_activity timestamp.

        Call this on each request to extend session validity.

        Args:
            session_id: Session to touch
        """
        session = self._sessions.get(session_id)
        if session is not None and session.is_valid:
            session.last_activity = self._get_current_time()

    def blacklist_token(self, access_token: str) -> None:
        """
        Add a token to the blacklist.

        Blacklisted tokens are immediately invalid even if the
        session hasn't been explicitly invalidated.

        Args:
            access_token: Token to blacklist
        """
        self._blacklisted_tokens.add(access_token)

        # Also invalidate the associated session
        session_id = self._token_to_session.get(access_token)
        if session_id is not None:
            session = self._sessions.get(session_id)
            if session is not None:
                invalidate_session(session, self._get_current_time())

    def is_token_blacklisted(self, access_token: str) -> bool:
        """
        Check if a token is blacklisted.

        Args:
            access_token: Token to check

        Returns:
            bool: True if token is blacklisted
        """
        return access_token in self._blacklisted_tokens

    def is_token_valid(self, access_token: str) -> bool:
        """
        Check if a token is valid (exists and not blacklisted).

        Args:
            access_token: Token to validate

        Returns:
            bool: True if token is valid
        """
        if access_token in self._blacklisted_tokens:
            return False

        session_id = self._token_to_session.get(access_token)
        if session_id is None:
            return False

        return self.is_session_valid(session_id)

    def cleanup_expired_sessions(self) -> int:
        """
        Remove expired sessions from storage.

        Call periodically to prevent memory bloat.

        Returns:
            int: Number of sessions cleaned up
        """
        current_time = self._get_current_time()
        expired_ids = []

        for session_id, session in self._sessions.items():
            if not is_session_valid(session, self.session_timeout_minutes, current_time):
                expired_ids.append(session_id)

        for session_id in expired_ids:
            session = self._sessions.pop(session_id, None)
            if session is not None:
                self._token_to_session.pop(session.access_token, None)

        return len(expired_ids)
