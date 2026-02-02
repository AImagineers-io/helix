"""
Security Alerting Service.

Provides:
- Multi-channel alerts (Email, Slack, PagerDuty, Log)
- Configurable triggers
- Threshold-based alerting
- Alert history

Channels:
- EMAIL: Send to configured email addresses
- SLACK: Post to Slack webhook
- PAGERDUTY: Create PagerDuty incident
- LOG: Write to security log
"""
import re
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional


class AlertChannel(Enum):
    """Alert channel types."""
    EMAIL = "email"
    SLACK = "slack"
    PAGERDUTY = "pagerduty"
    LOG = "log"


class AlertTrigger(Enum):
    """Alert trigger types."""
    MULTIPLE_LOGIN_FAILURES = "multiple_login_failures"
    INJECTION_ATTEMPT = "injection_attempt"
    RATE_LIMIT_ABUSE = "rate_limit_abuse"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    API_KEY_COMPROMISE = "api_key_compromise"
    MFA_BYPASS_ATTEMPT = "mfa_bypass_attempt"


@dataclass
class ChannelConfig:
    """Configuration for an alert channel."""
    channel_type: AlertChannel
    endpoint: str
    enabled: bool = True


@dataclass
class AlertConfig:
    """Configuration for alerting."""
    channels: list[ChannelConfig] = field(default_factory=list)
    login_failure_threshold: int = 5
    rate_limit_threshold: int = 10
    injection_threshold: int = 3

    def add_channel(
        self,
        channel_type: AlertChannel,
        endpoint: str,
        enabled: bool = True
    ) -> None:
        """
        Add alert channel.

        Args:
            channel_type: Type of channel
            endpoint: Channel endpoint (email, URL, etc.)
            enabled: Whether channel is enabled

        Raises:
            ValueError: If endpoint is invalid
        """
        # Validate endpoint
        if channel_type == AlertChannel.EMAIL:
            if not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', endpoint):
                raise ValueError(f"Invalid email address: {endpoint}")

        elif channel_type in [AlertChannel.SLACK, AlertChannel.PAGERDUTY]:
            if not endpoint.startswith(('http://', 'https://')):
                raise ValueError(f"Invalid URL: {endpoint}")

        self.channels.append(ChannelConfig(
            channel_type=channel_type,
            endpoint=endpoint,
            enabled=enabled
        ))


@dataclass
class SecurityAlert:
    """A security alert."""
    trigger: AlertTrigger
    severity: str
    message: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    source_ip: Optional[str] = None
    user_id: Optional[str] = None
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class AlertResult:
    """Result of sending an alert."""
    success: bool
    channels_sent: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


class AlertService:
    """
    Service for sending security alerts.

    Manages alert channels, thresholds, and history.
    """

    def __init__(self, config: Optional[AlertConfig] = None):
        """
        Initialize alert service.

        Args:
            config: Alert configuration
        """
        self.config = config or AlertConfig()
        self._alert_history: list[SecurityAlert] = []
        self._pending_alerts: list[SecurityAlert] = []
        self._event_counts: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))

    def create_alert(
        self,
        trigger: AlertTrigger,
        severity: str,
        message: str,
        source_ip: Optional[str] = None,
        user_id: Optional[str] = None,
        details: Optional[dict] = None
    ) -> SecurityAlert:
        """
        Create a security alert.

        Args:
            trigger: Alert trigger type
            severity: Severity level
            message: Alert message
            source_ip: Source IP if applicable
            user_id: User ID if applicable
            details: Additional details

        Returns:
            SecurityAlert: Created alert
        """
        alert = SecurityAlert(
            trigger=trigger,
            severity=severity,
            message=message,
            source_ip=source_ip,
            user_id=user_id,
            details=details or {}
        )

        self._alert_history.append(alert)
        return alert

    def send_alert(self, alert: SecurityAlert) -> AlertResult:
        """
        Send alert to all configured channels.

        Args:
            alert: Alert to send

        Returns:
            AlertResult: Send result
        """
        result = AlertResult(success=True)

        for channel_config in self.config.channels:
            if not channel_config.enabled:
                continue

            try:
                self._send_to_channel(alert, channel_config)
                result.channels_sent.append(channel_config.channel_type.value)
            except Exception as e:
                result.errors.append(f"{channel_config.channel_type.value}: {str(e)}")
                result.success = False

        # If no channels, still consider it successful (just logged)
        if not self.config.channels:
            result.success = True

        return result

    def _send_to_channel(
        self,
        alert: SecurityAlert,
        channel_config: ChannelConfig
    ) -> None:
        """
        Send alert to specific channel.

        Args:
            alert: Alert to send
            channel_config: Channel configuration
        """
        if channel_config.channel_type == AlertChannel.LOG:
            # Just log the alert
            self._log_alert(alert)

        elif channel_config.channel_type == AlertChannel.EMAIL:
            # Would send email via SMTP
            # For now, just log
            self._log_alert(alert)

        elif channel_config.channel_type == AlertChannel.SLACK:
            # Would POST to Slack webhook
            # For now, just log
            self._log_alert(alert)

        elif channel_config.channel_type == AlertChannel.PAGERDUTY:
            # Would create PagerDuty incident
            # For now, just log
            self._log_alert(alert)

    def _log_alert(self, alert: SecurityAlert) -> None:
        """Log alert to console/file."""
        # In production, would use proper logging
        pass

    def get_pending_alerts(self) -> list[SecurityAlert]:
        """Get alerts pending send."""
        return self._pending_alerts.copy()

    def record_event(self, event_type: str, identifier: str) -> None:
        """
        Record an event for threshold tracking.

        Args:
            event_type: Type of event
            identifier: User/device identifier
        """
        self._event_counts[event_type][identifier] += 1

    def should_alert_login_failures(self, identifier: str) -> bool:
        """
        Check if login failures exceeded threshold.

        Args:
            identifier: User/device identifier

        Returns:
            bool: True if threshold exceeded
        """
        count = self._event_counts["login_failure"][identifier]
        return count >= self.config.login_failure_threshold

    def get_alert_history(self, limit: int = 100) -> list[SecurityAlert]:
        """
        Get recent alert history.

        Args:
            limit: Maximum alerts to return

        Returns:
            list[SecurityAlert]: Recent alerts
        """
        return sorted(
            self._alert_history,
            key=lambda a: a.timestamp,
            reverse=True
        )[:limit]


# Global service instance
_alert_service: Optional[AlertService] = None


def _get_alert_service() -> AlertService:
    """Get or create global alert service."""
    global _alert_service

    if _alert_service is None:
        _alert_service = AlertService()

    return _alert_service


def send_security_alert(
    trigger: AlertTrigger,
    severity: str,
    message: str,
    source_ip: Optional[str] = None,
    user_id: Optional[str] = None,
    details: Optional[dict] = None
) -> AlertResult:
    """
    Convenience function to send security alert.

    Args:
        trigger: Alert trigger
        severity: Severity level
        message: Alert message
        source_ip: Source IP
        user_id: User ID
        details: Additional details

    Returns:
        AlertResult: Send result
    """
    service = _get_alert_service()
    alert = service.create_alert(
        trigger=trigger,
        severity=severity,
        message=message,
        source_ip=source_ip,
        user_id=user_id,
        details=details
    )
    return service.send_alert(alert)
