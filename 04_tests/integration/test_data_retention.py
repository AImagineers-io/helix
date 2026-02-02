"""
Integration tests for Data Retention (P12.5.5)

Tests data retention including:
- Configurable retention policies
- Data type specific retention
- Deletion scheduling
- Audit logging of deletions
"""
import pytest
from datetime import datetime, timedelta, timezone

from services.data_retention_service import (
    RetentionPolicy,
    RetentionConfig,
    DataRetentionService,
    get_retention_cutoff_date,
    is_record_expired,
    RetentionAction,
)


class TestRetentionPolicy:
    """Tests for retention policy configuration."""

    def test_default_conversations_policy(self):
        """Default conversations retention should be 30 days."""
        policy = RetentionPolicy(data_type="conversations")
        assert policy.retention_days == 30

    def test_default_logs_policy(self):
        """Default logs retention should be 90 days."""
        policy = RetentionPolicy(data_type="logs", retention_days=90)
        assert policy.retention_days == 90

    def test_custom_retention_days(self):
        """Custom retention days should be accepted."""
        policy = RetentionPolicy(data_type="analytics", retention_days=365)
        assert policy.retention_days == 365


class TestRetentionConfig:
    """Tests for retention configuration."""

    def test_multiple_policies(self):
        """Should support multiple data type policies."""
        config = RetentionConfig(policies=[
            RetentionPolicy("conversations", 30),
            RetentionPolicy("logs", 90),
            RetentionPolicy("analytics", 365),
        ])

        assert len(config.policies) == 3

    def test_get_policy_by_type(self):
        """Should retrieve policy by data type."""
        config = RetentionConfig(policies=[
            RetentionPolicy("conversations", 30),
            RetentionPolicy("logs", 90),
        ])

        policy = config.get_policy("conversations")
        assert policy.retention_days == 30

    def test_get_missing_policy_returns_default(self):
        """Missing policy should return default."""
        config = RetentionConfig(policies=[
            RetentionPolicy("logs", 90),
        ])

        policy = config.get_policy("conversations")
        assert policy.retention_days == config.default_retention_days


class TestCutoffDateCalculation:
    """Tests for cutoff date calculation."""

    def test_calculates_cutoff_date(self):
        """Should calculate correct cutoff date."""
        policy = RetentionPolicy("test", retention_days=30)
        cutoff = get_retention_cutoff_date(policy)

        expected = datetime.now(timezone.utc) - timedelta(days=30)

        # Allow 1 second tolerance
        assert abs((cutoff - expected).total_seconds()) < 1

    def test_cutoff_for_different_periods(self):
        """Should handle different retention periods."""
        policy_30 = RetentionPolicy("short", retention_days=30)
        policy_90 = RetentionPolicy("medium", retention_days=90)
        policy_365 = RetentionPolicy("long", retention_days=365)

        cutoff_30 = get_retention_cutoff_date(policy_30)
        cutoff_90 = get_retention_cutoff_date(policy_90)
        cutoff_365 = get_retention_cutoff_date(policy_365)

        # Longer retention = earlier cutoff
        assert cutoff_30 > cutoff_90 > cutoff_365


class TestRecordExpiration:
    """Tests for record expiration checking."""

    def test_old_record_is_expired(self):
        """Old record should be marked as expired."""
        policy = RetentionPolicy("test", retention_days=30)
        old_date = datetime.now(timezone.utc) - timedelta(days=45)

        assert is_record_expired(old_date, policy) is True

    def test_recent_record_not_expired(self):
        """Recent record should not be expired."""
        policy = RetentionPolicy("test", retention_days=30)
        recent_date = datetime.now(timezone.utc) - timedelta(days=15)

        assert is_record_expired(recent_date, policy) is False

    def test_boundary_record(self):
        """Record just inside retention should not be expired."""
        policy = RetentionPolicy("test", retention_days=30)
        # Slightly less than 30 days ago (29 days, 23 hours)
        boundary_date = datetime.now(timezone.utc) - timedelta(days=29, hours=23)

        # Should NOT be expired (still within retention)
        assert is_record_expired(boundary_date, policy) is False


class TestDataRetentionService:
    """Tests for DataRetentionService class."""

    @pytest.fixture
    def service(self):
        """Create retention service."""
        config = RetentionConfig(policies=[
            RetentionPolicy("conversations", 30),
            RetentionPolicy("logs", 90),
        ])
        return DataRetentionService(config)

    def test_identifies_expired_records(self, service):
        """Should identify records past retention."""
        records = [
            {"id": 1, "created_at": datetime.now(timezone.utc) - timedelta(days=45)},
            {"id": 2, "created_at": datetime.now(timezone.utc) - timedelta(days=15)},
            {"id": 3, "created_at": datetime.now(timezone.utc) - timedelta(days=60)},
        ]

        expired = service.find_expired_records(records, "conversations")

        assert len(expired) == 2
        assert any(r["id"] == 1 for r in expired)
        assert any(r["id"] == 3 for r in expired)

    def test_creates_retention_action(self, service):
        """Should create retention action for deletion."""
        records = [
            {"id": 1, "created_at": datetime.now(timezone.utc) - timedelta(days=45)},
        ]

        action = service.create_retention_action(
            data_type="conversations",
            records=records
        )

        assert action.data_type == "conversations"
        assert action.record_count == 1

    def test_logs_deletion(self, service):
        """Should log deletion actions."""
        action = RetentionAction(
            data_type="conversations",
            record_count=10,
            timestamp=datetime.now(timezone.utc)
        )

        log_entry = service.create_audit_log(action)

        assert log_entry["action"] == "data_retention_delete"
        assert log_entry["data_type"] == "conversations"
        assert log_entry["record_count"] == 10


class TestRetentionAction:
    """Tests for RetentionAction."""

    def test_action_has_timestamp(self):
        """Action should have timestamp."""
        action = RetentionAction(
            data_type="test",
            record_count=5,
            timestamp=datetime.now(timezone.utc)
        )

        assert action.timestamp is not None

    def test_action_has_record_count(self):
        """Action should track record count."""
        action = RetentionAction(
            data_type="test",
            record_count=100,
            timestamp=datetime.now(timezone.utc)
        )

        assert action.record_count == 100


class TestDryRun:
    """Tests for dry run functionality."""

    @pytest.fixture
    def service(self):
        config = RetentionConfig(policies=[
            RetentionPolicy("conversations", 30),
        ])
        return DataRetentionService(config)

    def test_dry_run_identifies_but_doesnt_delete(self, service):
        """Dry run should identify but not delete."""
        records = [
            {"id": 1, "created_at": datetime.now(timezone.utc) - timedelta(days=45)},
        ]

        result = service.execute_retention(
            data_type="conversations",
            records=records,
            dry_run=True
        )

        assert result.would_delete == 1
        assert result.actually_deleted == 0


class TestRetentionScheduling:
    """Tests for retention scheduling."""

    @pytest.fixture
    def service(self):
        config = RetentionConfig(policies=[
            RetentionPolicy("conversations", 30),
        ])
        return DataRetentionService(config)

    def test_get_next_run_time(self, service):
        """Should calculate next scheduled run."""
        # Assuming daily runs
        next_run = service.get_next_scheduled_run()
        assert next_run is not None

    def test_is_retention_due(self, service):
        """Should check if retention is due."""
        # With no last run, should be due
        assert service.is_retention_due() is True
