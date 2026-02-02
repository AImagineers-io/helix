"""
Integration tests for Data Access Audit Trail (P12.8.4)

Tests audit trail including:
- Track who accessed what data
- Track when data was accessed
- Configurable retention
- Query capabilities
"""
import pytest
from datetime import datetime, timezone

from services.data_audit import (
    DataAccessLog,
    DataAccessType,
    DataAuditService,
    log_data_access,
    get_access_history,
)


class TestDataAccessType:
    """Tests for data access types."""

    def test_access_types(self):
        """Should have expected access types."""
        assert DataAccessType.READ is not None
        assert DataAccessType.WRITE is not None
        assert DataAccessType.DELETE is not None
        assert DataAccessType.EXPORT is not None


class TestDataAccessLog:
    """Tests for DataAccessLog model."""

    def test_log_has_timestamp(self):
        """Log should have timestamp."""
        log = DataAccessLog(
            user_id="admin1",
            data_type="conversations",
            access_type=DataAccessType.READ,
            record_id="conv_123"
        )

        assert log.timestamp is not None

    def test_log_has_required_fields(self):
        """Log should have required fields."""
        log = DataAccessLog(
            user_id="admin2",
            data_type="qa_pairs",
            access_type=DataAccessType.WRITE,
            record_id="qa_456"
        )

        assert log.user_id == "admin2"
        assert log.data_type == "qa_pairs"
        assert log.access_type == DataAccessType.WRITE


class TestDataAuditService:
    """Tests for DataAuditService class."""

    @pytest.fixture
    def service(self):
        """Create audit service."""
        return DataAuditService()

    def test_log_access(self, service):
        """Should log data access."""
        log = service.log_access(
            user_id="user1",
            data_type="conversations",
            access_type=DataAccessType.READ,
            record_id="conv_1"
        )

        assert log.log_id is not None

    def test_get_access_by_user(self, service):
        """Should get access logs by user."""
        service.log_access("user2", "data", DataAccessType.READ, "rec1")
        service.log_access("user2", "data", DataAccessType.READ, "rec2")
        service.log_access("user3", "data", DataAccessType.READ, "rec3")

        logs = service.get_access_by_user("user2")

        assert len(logs) == 2

    def test_get_access_by_record(self, service):
        """Should get access logs by record."""
        service.log_access("user1", "data", DataAccessType.READ, "record_x")
        service.log_access("user2", "data", DataAccessType.WRITE, "record_x")

        logs = service.get_access_by_record("record_x")

        assert len(logs) == 2


class TestAccessHistory:
    """Tests for access history queries."""

    @pytest.fixture
    def service(self):
        return DataAuditService()

    def test_get_recent_access(self, service):
        """Should get recent access logs."""
        for i in range(10):
            service.log_access(f"user{i}", "data", DataAccessType.READ, f"rec{i}")

        recent = service.get_recent_access(limit=5)

        assert len(recent) == 5

    def test_filter_by_access_type(self, service):
        """Should filter by access type."""
        service.log_access("user1", "data", DataAccessType.READ, "rec1")
        service.log_access("user2", "data", DataAccessType.WRITE, "rec2")
        service.log_access("user3", "data", DataAccessType.DELETE, "rec3")

        writes = service.get_by_access_type(DataAccessType.WRITE)

        assert all(log.access_type == DataAccessType.WRITE for log in writes)

    def test_filter_by_data_type(self, service):
        """Should filter by data type."""
        service.log_access("user1", "conversations", DataAccessType.READ, "c1")
        service.log_access("user2", "qa_pairs", DataAccessType.READ, "q1")
        service.log_access("user3", "conversations", DataAccessType.READ, "c2")

        conv_logs = service.get_by_data_type("conversations")

        assert len(conv_logs) == 2


class TestAuditRetention:
    """Tests for audit log retention."""

    @pytest.fixture
    def service(self):
        return DataAuditService(retention_days=365)

    def test_retention_config(self, service):
        """Should have configurable retention."""
        assert service.retention_days == 365

    def test_get_logs_count(self, service):
        """Should return total log count."""
        service.log_access("u1", "d", DataAccessType.READ, "r1")
        service.log_access("u2", "d", DataAccessType.READ, "r2")

        count = service.get_total_count()

        assert count >= 2


class TestLogDetails:
    """Tests for log detail fields."""

    @pytest.fixture
    def service(self):
        return DataAuditService()

    def test_stores_ip_address(self, service):
        """Should store IP address."""
        log = service.log_access(
            user_id="user1",
            data_type="data",
            access_type=DataAccessType.READ,
            record_id="rec1",
            ip_address="192.168.1.1"
        )

        assert log.ip_address == "192.168.1.1"

    def test_stores_extra_details(self, service):
        """Should store extra details."""
        log = service.log_access(
            user_id="user2",
            data_type="data",
            access_type=DataAccessType.EXPORT,
            record_id="rec2",
            details={"reason": "DSAR request", "request_id": "dsar_123"}
        )

        assert log.details["reason"] == "DSAR request"


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_log_data_access_function(self):
        """Should log access via function."""
        log = log_data_access(
            user_id="func_user",
            data_type="test_data",
            access_type=DataAccessType.READ,
            record_id="test_record"
        )

        assert log.log_id is not None

    def test_get_access_history_function(self):
        """Should get history via function."""
        log_data_access("hist_user", "data", DataAccessType.READ, "rec1")

        history = get_access_history(user_id="hist_user")

        assert len(history) >= 1


class TestAuditExport:
    """Tests for audit log export."""

    @pytest.fixture
    def service(self):
        return DataAuditService()

    def test_export_logs(self, service):
        """Should export logs."""
        service.log_access("u1", "d", DataAccessType.READ, "r1")
        service.log_access("u2", "d", DataAccessType.WRITE, "r2")

        export = service.export_logs()

        assert len(export) >= 2
        assert all("user_id" in log for log in export)

    def test_export_is_json_serializable(self, service):
        """Export should be JSON serializable."""
        service.log_access("u1", "d", DataAccessType.READ, "r1")

        export = service.export_logs()

        import json
        json_str = json.dumps(export, default=str)
        assert json_str is not None
