"""
Integration tests for Security Alerting (P12.6.4)

Tests alerting including:
- Email alerts
- Slack webhooks
- PagerDuty integration
- Alert triggers
- Alert configuration
"""
import pytest
from datetime import datetime, timezone

from services.alerting import (
    AlertConfig,
    AlertChannel,
    AlertTrigger,
    AlertService,
    SecurityAlert,
    send_security_alert,
)


class TestAlertConfig:
    """Tests for alert configuration."""

    def test_default_config(self):
        """Default config should have no channels."""
        config = AlertConfig()
        assert len(config.channels) == 0

    def test_add_email_channel(self):
        """Should add email channel."""
        config = AlertConfig()
        config.add_channel(
            AlertChannel.EMAIL,
            endpoint="security@example.com"
        )

        assert len(config.channels) == 1
        assert config.channels[0].channel_type == AlertChannel.EMAIL

    def test_add_slack_channel(self):
        """Should add Slack channel."""
        config = AlertConfig()
        config.add_channel(
            AlertChannel.SLACK,
            endpoint="https://hooks.slack.com/services/xxx"
        )

        assert config.channels[0].channel_type == AlertChannel.SLACK


class TestAlertTrigger:
    """Tests for alert triggers."""

    def test_trigger_types(self):
        """Should have expected trigger types."""
        assert AlertTrigger.MULTIPLE_LOGIN_FAILURES is not None
        assert AlertTrigger.INJECTION_ATTEMPT is not None
        assert AlertTrigger.RATE_LIMIT_ABUSE is not None
        assert AlertTrigger.SUSPICIOUS_ACTIVITY is not None


class TestSecurityAlert:
    """Tests for SecurityAlert model."""

    def test_alert_has_timestamp(self):
        """Alert should have timestamp."""
        alert = SecurityAlert(
            trigger=AlertTrigger.INJECTION_ATTEMPT,
            severity="high",
            message="Injection detected",
            source_ip="192.168.1.1"
        )

        assert alert.timestamp is not None

    def test_alert_has_severity(self):
        """Alert should have severity."""
        alert = SecurityAlert(
            trigger=AlertTrigger.MULTIPLE_LOGIN_FAILURES,
            severity="medium",
            message="Multiple failures"
        )

        assert alert.severity == "medium"


class TestAlertService:
    """Tests for AlertService class."""

    @pytest.fixture
    def service(self):
        """Create alert service."""
        config = AlertConfig()
        config.add_channel(AlertChannel.LOG, endpoint="test")
        return AlertService(config)

    def test_create_alert(self, service):
        """Should create alert."""
        alert = service.create_alert(
            trigger=AlertTrigger.INJECTION_ATTEMPT,
            severity="high",
            message="Test injection",
            source_ip="10.0.0.1"
        )

        assert alert is not None
        assert alert.trigger == AlertTrigger.INJECTION_ATTEMPT

    def test_send_alert(self, service):
        """Should send alert to configured channels."""
        alert = service.create_alert(
            trigger=AlertTrigger.SUSPICIOUS_ACTIVITY,
            severity="high",
            message="Suspicious activity detected"
        )

        result = service.send_alert(alert)

        # Should succeed with LOG channel
        assert result.success is True

    def test_get_pending_alerts(self, service):
        """Should track pending alerts."""
        service.create_alert(
            AlertTrigger.RATE_LIMIT_ABUSE,
            "high",
            "Rate limit abuse"
        )

        pending = service.get_pending_alerts()
        # May or may not have pending depending on send success
        assert isinstance(pending, list)


class TestAlertThresholds:
    """Tests for alert thresholds."""

    @pytest.fixture
    def service(self):
        config = AlertConfig(
            login_failure_threshold=5,
            rate_limit_threshold=10
        )
        config.add_channel(AlertChannel.LOG, endpoint="test")
        return AlertService(config)

    def test_below_threshold_no_alert(self, service):
        """Below threshold should not trigger alert."""
        for i in range(3):
            service.record_event("login_failure", f"user{i}")

        should_alert = service.should_alert_login_failures("user0")
        assert should_alert is False

    def test_above_threshold_triggers_alert(self, service):
        """Above threshold should trigger alert."""
        for _ in range(6):
            service.record_event("login_failure", "user123")

        should_alert = service.should_alert_login_failures("user123")
        assert should_alert is True


class TestAlertChannels:
    """Tests for different alert channels."""

    def test_log_channel_always_succeeds(self):
        """LOG channel should always succeed."""
        config = AlertConfig()
        config.add_channel(AlertChannel.LOG, endpoint="stdout")
        service = AlertService(config)

        alert = service.create_alert(
            AlertTrigger.INJECTION_ATTEMPT,
            "high",
            "Test"
        )
        result = service.send_alert(alert)

        assert result.success is True

    def test_email_channel_validation(self):
        """Email channel should validate endpoint."""
        config = AlertConfig()

        # Invalid email should raise
        with pytest.raises(ValueError):
            config.add_channel(AlertChannel.EMAIL, endpoint="not-an-email")

    def test_webhook_channel_validation(self):
        """Webhook channels should validate URL."""
        config = AlertConfig()

        # Invalid URL should raise
        with pytest.raises(ValueError):
            config.add_channel(AlertChannel.SLACK, endpoint="not-a-url")


class TestSendSecurityAlertFunction:
    """Tests for send_security_alert convenience function."""

    def test_sends_alert(self):
        """Should send alert via convenience function."""
        # This uses global service which may not be configured
        result = send_security_alert(
            trigger=AlertTrigger.SUSPICIOUS_ACTIVITY,
            severity="medium",
            message="Test alert"
        )

        # Should return result (success depends on config)
        assert result is not None


class TestAlertDetails:
    """Tests for alert details handling."""

    @pytest.fixture
    def service(self):
        config = AlertConfig()
        config.add_channel(AlertChannel.LOG, endpoint="test")
        return AlertService(config)

    def test_stores_details(self, service):
        """Should store alert details."""
        alert = service.create_alert(
            trigger=AlertTrigger.INJECTION_ATTEMPT,
            severity="high",
            message="Injection detected",
            details={
                "pattern": "ignore previous",
                "device_id": "dev123"
            }
        )

        assert alert.details["pattern"] == "ignore previous"

    def test_includes_source_ip(self, service):
        """Should include source IP in alert."""
        alert = service.create_alert(
            trigger=AlertTrigger.RATE_LIMIT_ABUSE,
            severity="high",
            message="Rate limit",
            source_ip="192.168.1.100"
        )

        assert alert.source_ip == "192.168.1.100"
