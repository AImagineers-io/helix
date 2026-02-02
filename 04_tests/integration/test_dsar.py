"""
Integration tests for Data Subject Access Request (P12.8.2)

Tests DSAR support including:
- Export user data
- Data anonymization
- Data deletion
- Request tracking
"""
import pytest
from datetime import datetime, timezone

from services.dsar_service import (
    DSARRequest,
    DSARType,
    DSARStatus,
    DSARService,
    create_dsar_request,
    process_dsar_request,
)


class TestDSARType:
    """Tests for DSAR request types."""

    def test_request_types(self):
        """Should have expected request types."""
        assert DSARType.ACCESS is not None
        assert DSARType.DELETION is not None
        assert DSARType.RECTIFICATION is not None
        assert DSARType.PORTABILITY is not None


class TestDSARStatus:
    """Tests for DSAR status."""

    def test_status_values(self):
        """Should have expected status values."""
        assert DSARStatus.PENDING is not None
        assert DSARStatus.PROCESSING is not None
        assert DSARStatus.COMPLETED is not None
        assert DSARStatus.REJECTED is not None


class TestDSARRequest:
    """Tests for DSARRequest model."""

    def test_request_has_id(self):
        """Request should have ID."""
        request = DSARRequest(
            user_id="user123",
            request_type=DSARType.ACCESS,
            email="user@example.com"
        )

        assert request.request_id is not None

    def test_request_has_timestamp(self):
        """Request should have timestamp."""
        request = DSARRequest(
            user_id="user456",
            request_type=DSARType.DELETION,
            email="user@example.com"
        )

        assert request.created_at is not None


class TestDSARService:
    """Tests for DSARService class."""

    @pytest.fixture
    def service(self):
        """Create DSAR service."""
        return DSARService()

    def test_create_request(self, service):
        """Should create DSAR request."""
        request = service.create_request(
            user_id="user1",
            request_type=DSARType.ACCESS,
            email="user1@example.com"
        )

        assert request.request_id is not None
        assert request.status == DSARStatus.PENDING

    def test_get_request(self, service):
        """Should retrieve request by ID."""
        created = service.create_request(
            user_id="user2",
            request_type=DSARType.ACCESS,
            email="user2@example.com"
        )

        retrieved = service.get_request(created.request_id)

        assert retrieved.request_id == created.request_id

    def test_update_status(self, service):
        """Should update request status."""
        request = service.create_request(
            user_id="user3",
            request_type=DSARType.ACCESS,
            email="user3@example.com"
        )

        service.update_status(request.request_id, DSARStatus.PROCESSING)
        updated = service.get_request(request.request_id)

        assert updated.status == DSARStatus.PROCESSING


class TestDataExport:
    """Tests for data export functionality."""

    @pytest.fixture
    def service(self):
        return DSARService()

    def test_export_user_data(self, service):
        """Should export user data."""
        # Create some mock data
        service.add_user_data("export_user", "conversations", [
            {"id": 1, "message": "Hello"},
            {"id": 2, "message": "World"},
        ])

        export = service.export_user_data("export_user")

        assert "conversations" in export
        assert len(export["conversations"]) == 2

    def test_export_format_json(self, service):
        """Export should be JSON serializable."""
        service.add_user_data("json_user", "profile", {"name": "Test"})

        export = service.export_user_data("json_user")

        import json
        # Should not raise
        json_str = json.dumps(export)
        assert json_str is not None

    def test_export_includes_metadata(self, service):
        """Export should include metadata."""
        export = service.export_user_data("meta_user")

        assert "export_timestamp" in export
        assert "user_id" in export


class TestDataDeletion:
    """Tests for data deletion functionality."""

    @pytest.fixture
    def service(self):
        return DSARService()

    def test_delete_user_data(self, service):
        """Should delete user data."""
        service.add_user_data("delete_user", "conversations", [{"id": 1}])

        result = service.delete_user_data("delete_user")

        assert result.success is True

    def test_deletion_is_complete(self, service):
        """Should verify deletion completeness."""
        service.add_user_data("complete_user", "data", {"key": "value"})
        service.delete_user_data("complete_user")

        export = service.export_user_data("complete_user")

        # Should have no data
        assert "data" not in export or len(export.get("data", [])) == 0


class TestDataAnonymization:
    """Tests for data anonymization."""

    @pytest.fixture
    def service(self):
        return DSARService()

    def test_anonymize_user_data(self, service):
        """Should anonymize user data."""
        service.add_user_data("anon_user", "profile", {
            "name": "John Doe",
            "email": "john@example.com"
        })

        result = service.anonymize_user_data("anon_user")

        assert result.success is True

    def test_anonymization_removes_pii(self, service):
        """Anonymization should remove PII."""
        service.add_user_data("pii_user", "profile", {
            "name": "Jane Doe",
            "email": "jane@example.com",
            "phone": "555-1234"
        })

        service.anonymize_user_data("pii_user")
        export = service.export_user_data("pii_user")

        # PII fields should be anonymized
        if "profile" in export and export["profile"]:
            profile = export["profile"]
            if isinstance(profile, dict):
                assert profile.get("email") != "jane@example.com"


class TestRequestTracking:
    """Tests for request tracking."""

    @pytest.fixture
    def service(self):
        return DSARService()

    def test_list_requests(self, service):
        """Should list all requests."""
        service.create_request("user1", DSARType.ACCESS, "user1@test.com")
        service.create_request("user2", DSARType.DELETION, "user2@test.com")

        requests = service.list_requests()

        assert len(requests) >= 2

    def test_filter_by_status(self, service):
        """Should filter requests by status."""
        req = service.create_request("user3", DSARType.ACCESS, "user3@test.com")
        service.update_status(req.request_id, DSARStatus.COMPLETED)

        completed = service.list_requests(status=DSARStatus.COMPLETED)

        assert all(r.status == DSARStatus.COMPLETED for r in completed)


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_create_dsar_request_function(self):
        """Should create request via function."""
        request = create_dsar_request(
            user_id="func_user",
            request_type=DSARType.ACCESS,
            email="func@test.com"
        )

        assert request.request_id is not None

    def test_process_dsar_request_function(self):
        """Should process request via function."""
        request = create_dsar_request(
            user_id="process_user",
            request_type=DSARType.ACCESS,
            email="process@test.com"
        )

        result = process_dsar_request(request.request_id)

        assert result is not None
