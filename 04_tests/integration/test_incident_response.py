"""
Integration tests for Incident Response Automation (P12.6.5)

Tests incident response including:
- Auto-block IP/device
- Force session invalidation
- Log snapshot
- Configurable thresholds
"""
import pytest
from datetime import datetime, timezone

from services.incident_response import (
    IncidentConfig,
    IncidentResponse,
    IncidentAction,
    IncidentService,
    create_incident,
    execute_response,
)


class TestIncidentConfig:
    """Tests for incident configuration."""

    def test_default_thresholds(self):
        """Default thresholds should be set."""
        config = IncidentConfig()
        assert config.auto_block_threshold > 0
        assert config.session_invalidation_threshold > 0

    def test_custom_thresholds(self):
        """Custom thresholds should be accepted."""
        config = IncidentConfig(
            auto_block_threshold=10,
            session_invalidation_threshold=5
        )
        assert config.auto_block_threshold == 10


class TestIncidentAction:
    """Tests for incident actions."""

    def test_action_types(self):
        """Should have expected action types."""
        assert IncidentAction.BLOCK_IP is not None
        assert IncidentAction.BLOCK_DEVICE is not None
        assert IncidentAction.INVALIDATE_SESSION is not None
        assert IncidentAction.SNAPSHOT_LOGS is not None
        assert IncidentAction.ALERT is not None


class TestIncidentResponse:
    """Tests for IncidentResponse model."""

    def test_response_has_timestamp(self):
        """Response should have timestamp."""
        response = IncidentResponse(
            incident_id="inc_123",
            actions=[IncidentAction.ALERT],
            reason="Test incident"
        )

        assert response.timestamp is not None

    def test_response_has_actions(self):
        """Response should have actions."""
        response = IncidentResponse(
            incident_id="inc_456",
            actions=[IncidentAction.BLOCK_IP, IncidentAction.ALERT],
            reason="Multiple violations"
        )

        assert len(response.actions) == 2


class TestIncidentService:
    """Tests for IncidentService class."""

    @pytest.fixture
    def service(self):
        """Create incident service."""
        config = IncidentConfig(
            auto_block_threshold=5,
            block_duration_minutes=30
        )
        return IncidentService(config)

    def test_record_violation(self, service):
        """Should record violation."""
        service.record_violation(
            source_ip="192.168.1.1",
            violation_type="injection_attempt"
        )

        count = service.get_violation_count("192.168.1.1")
        assert count == 1

    def test_auto_block_on_threshold(self, service):
        """Should auto-block after threshold violations."""
        for _ in range(6):
            service.record_violation(
                source_ip="192.168.1.100",
                violation_type="rate_limit"
            )

        assert service.is_ip_blocked("192.168.1.100") is True

    def test_create_incident(self, service):
        """Should create incident record."""
        incident = service.create_incident(
            source_ip="10.0.0.1",
            incident_type="suspicious_activity",
            details={"pattern": "repeated injection"}
        )

        assert incident.incident_id is not None
        assert incident.source_ip == "10.0.0.1"

    def test_execute_response(self, service):
        """Should execute incident response."""
        incident = service.create_incident(
            source_ip="10.0.0.2",
            incident_type="critical_violation"
        )

        response = service.execute_response(
            incident,
            actions=[IncidentAction.BLOCK_IP, IncidentAction.ALERT]
        )

        assert response.success is True
        assert IncidentAction.BLOCK_IP in response.actions_executed


class TestAutoBlock:
    """Tests for auto-blocking."""

    @pytest.fixture
    def service(self):
        config = IncidentConfig(auto_block_threshold=3)
        return IncidentService(config)

    def test_block_ip(self, service):
        """Should block IP address."""
        service.block_ip("192.168.1.50", duration_minutes=60)

        assert service.is_ip_blocked("192.168.1.50") is True

    def test_block_device(self, service):
        """Should block device."""
        service.block_device("device_123", duration_minutes=60)

        assert service.is_device_blocked("device_123") is True

    def test_unblock_ip(self, service):
        """Should unblock IP."""
        service.block_ip("192.168.1.60", duration_minutes=60)
        service.unblock_ip("192.168.1.60")

        assert service.is_ip_blocked("192.168.1.60") is False


class TestSessionInvalidation:
    """Tests for session invalidation."""

    @pytest.fixture
    def service(self):
        return IncidentService()

    def test_invalidate_sessions_for_ip(self, service):
        """Should invalidate sessions for IP."""
        result = service.invalidate_sessions_for_ip("192.168.1.1")

        assert result.success is True

    def test_invalidate_sessions_for_user(self, service):
        """Should invalidate sessions for user."""
        result = service.invalidate_sessions_for_user("user123")

        assert result.success is True


class TestLogSnapshot:
    """Tests for log snapshot functionality."""

    @pytest.fixture
    def service(self):
        return IncidentService()

    def test_create_log_snapshot(self, service):
        """Should create log snapshot for incident."""
        incident = service.create_incident(
            source_ip="10.0.0.5",
            incident_type="investigation"
        )

        snapshot = service.create_log_snapshot(incident)

        assert snapshot is not None
        assert snapshot.incident_id == incident.incident_id

    def test_snapshot_includes_timerange(self, service):
        """Snapshot should include time range."""
        incident = service.create_incident(
            source_ip="10.0.0.6",
            incident_type="investigation"
        )

        snapshot = service.create_log_snapshot(
            incident,
            hours_before=2,
            hours_after=1
        )

        assert snapshot.time_range_start is not None
        assert snapshot.time_range_end is not None


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_create_incident_function(self):
        """Should create incident via function."""
        incident = create_incident(
            source_ip="10.0.0.10",
            incident_type="test"
        )

        assert incident is not None

    def test_execute_response_function(self):
        """Should execute response via function."""
        incident = create_incident(
            source_ip="10.0.0.11",
            incident_type="test"
        )

        result = execute_response(
            incident,
            actions=[IncidentAction.ALERT]
        )

        assert result.success is True


class TestIncidentHistory:
    """Tests for incident history tracking."""

    @pytest.fixture
    def service(self):
        return IncidentService()

    def test_get_incident_history(self, service):
        """Should retrieve incident history."""
        service.create_incident("10.0.0.1", "test1")
        service.create_incident("10.0.0.2", "test2")

        history = service.get_incident_history(limit=10)

        assert len(history) >= 2

    def test_get_incidents_by_ip(self, service):
        """Should filter incidents by IP."""
        service.create_incident("192.168.1.1", "test")
        service.create_incident("192.168.1.2", "test")
        service.create_incident("192.168.1.1", "test2")

        incidents = service.get_incidents_by_ip("192.168.1.1")

        assert len(incidents) == 2
