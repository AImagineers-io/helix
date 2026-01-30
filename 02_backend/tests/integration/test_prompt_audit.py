"""
Integration tests for prompt audit logging.

Tests that all prompt changes are logged with user/timestamp.
"""
import os
import pytest

# Set required environment variables BEFORE importing app
os.environ['APP_NAME'] = 'TestApp'
os.environ['BOT_NAME'] = 'TestBot'
os.environ['DATABASE_URL'] = 'sqlite:///:memory:?cache=shared'
os.environ['API_KEY'] = 'test-api-key'

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from database.connection import Base, get_db
from api.main import app


@pytest.fixture(scope="function")
def db_session():
    """Create an isolated database session for each test."""
    engine = create_engine(
        "sqlite:///:memory:?cache=shared",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(db_session):
    """Create test client with overridden database."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers():
    """Return headers with API key authentication."""
    return {"X-API-Key": "test-api-key"}


class TestPromptAuditLogging:
    """Test suite for prompt audit logging."""

    def test_create_prompt_creates_audit_log(self, client, auth_headers):
        """Test that creating a prompt creates an audit log entry."""
        # Act: Create a prompt
        create_response = client.post(
            "/prompts",
            json={
                "name": "test_prompt",
                "prompt_type": "system_prompt",
                "content": "Test content"
            },
            headers=auth_headers
        )
        assert create_response.status_code == 201
        template_id = create_response.json()["id"]

        # Assert: Check audit log
        audit_response = client.get(
            f"/prompts/{template_id}/audit",
            headers=auth_headers
        )
        assert audit_response.status_code == 200
        audit_logs = audit_response.json()

        assert len(audit_logs) >= 1
        create_log = audit_logs[0]
        assert create_log["action"] == "create"
        assert create_log["template_id"] == template_id
        assert "timestamp" in create_log

    def test_update_prompt_creates_audit_log(self, client, auth_headers):
        """Test that updating a prompt creates an audit log entry."""
        # Arrange: Create a prompt
        create_response = client.post(
            "/prompts",
            json={
                "name": "test_prompt",
                "prompt_type": "system_prompt",
                "content": "Initial content"
            },
            headers=auth_headers
        )
        template = create_response.json()
        template_id = template["id"]

        # Act: Update the prompt
        client.put(
            f"/prompts/{template_id}",
            json={
                "content": "Updated content",
                "edit_version": template["edit_version"]
            },
            headers=auth_headers
        )

        # Assert: Check audit log
        audit_response = client.get(
            f"/prompts/{template_id}/audit",
            headers=auth_headers
        )
        audit_logs = audit_response.json()

        # Should have create + update entries
        assert len(audit_logs) >= 2
        update_log = next((log for log in audit_logs if log["action"] == "update"), None)
        assert update_log is not None
        assert update_log["template_id"] == template_id

    def test_publish_version_creates_audit_log(self, client, auth_headers):
        """Test that publishing a version creates an audit log entry."""
        # Arrange: Create prompt with two versions
        create_response = client.post(
            "/prompts",
            json={
                "name": "test_prompt",
                "prompt_type": "system_prompt",
                "content": "Version 1"
            },
            headers=auth_headers
        )
        template = create_response.json()
        template_id = template["id"]

        # Create version 2
        update_response = client.put(
            f"/prompts/{template_id}",
            json={
                "content": "Version 2",
                "edit_version": template["edit_version"]
            },
            headers=auth_headers
        )

        # Act: Publish version 1
        client.post(
            f"/prompts/{template_id}/publish",
            json={"version_number": 1},
            headers=auth_headers
        )

        # Assert: Check audit log
        audit_response = client.get(
            f"/prompts/{template_id}/audit",
            headers=auth_headers
        )
        audit_logs = audit_response.json()

        publish_log = next((log for log in audit_logs if log["action"] == "publish"), None)
        assert publish_log is not None
        assert publish_log["details"]["version_number"] == 1

    def test_rollback_creates_audit_log(self, client, auth_headers):
        """Test that rollback creates an audit log entry."""
        # Arrange: Create prompt with two versions
        create_response = client.post(
            "/prompts",
            json={
                "name": "test_prompt",
                "prompt_type": "system_prompt",
                "content": "Version 1"
            },
            headers=auth_headers
        )
        template = create_response.json()
        template_id = template["id"]

        # Create version 2
        client.put(
            f"/prompts/{template_id}",
            json={
                "content": "Version 2",
                "edit_version": template["edit_version"]
            },
            headers=auth_headers
        )

        # Act: Rollback
        client.post(
            f"/prompts/{template_id}/rollback",
            headers=auth_headers
        )

        # Assert: Check audit log
        audit_response = client.get(
            f"/prompts/{template_id}/audit",
            headers=auth_headers
        )
        audit_logs = audit_response.json()

        rollback_log = next((log for log in audit_logs if log["action"] == "rollback"), None)
        assert rollback_log is not None

    def test_audit_log_contains_api_key_hash(self, client, auth_headers):
        """Test that audit log contains hashed API key for tracking."""
        # Act: Create a prompt
        create_response = client.post(
            "/prompts",
            json={
                "name": "test_prompt",
                "prompt_type": "system_prompt",
                "content": "Test content"
            },
            headers=auth_headers
        )
        template_id = create_response.json()["id"]

        # Assert: Check audit log has admin_key_hash
        audit_response = client.get(
            f"/prompts/{template_id}/audit",
            headers=auth_headers
        )
        audit_logs = audit_response.json()

        assert len(audit_logs) >= 1
        # Should have a hash, not the actual key
        assert "admin_key_hash" in audit_logs[0]
        assert audit_logs[0]["admin_key_hash"] != "test-api-key"  # Not plain text

    def test_audit_log_ordered_by_timestamp_desc(self, client, auth_headers):
        """Test that audit logs are ordered newest first."""
        # Arrange: Create and update prompt
        create_response = client.post(
            "/prompts",
            json={
                "name": "test_prompt",
                "prompt_type": "system_prompt",
                "content": "Version 1"
            },
            headers=auth_headers
        )
        template = create_response.json()
        template_id = template["id"]

        client.put(
            f"/prompts/{template_id}",
            json={
                "content": "Version 2",
                "edit_version": template["edit_version"]
            },
            headers=auth_headers
        )

        # Assert: Check order
        audit_response = client.get(
            f"/prompts/{template_id}/audit",
            headers=auth_headers
        )
        audit_logs = audit_response.json()

        # Most recent should be first
        assert audit_logs[0]["action"] == "update"
        assert audit_logs[1]["action"] == "create"


class TestAuditLogModel:
    """Test suite for PromptAuditLog model."""

    def test_audit_log_model_exists(self, db_session):
        """Test that PromptAuditLog model exists."""
        from database.models import PromptAuditLog

        assert PromptAuditLog is not None

    def test_audit_log_has_required_fields(self, db_session):
        """Test that audit log has all required fields."""
        from database.models import PromptAuditLog

        # Check columns exist
        assert hasattr(PromptAuditLog, 'id')
        assert hasattr(PromptAuditLog, 'template_id')
        assert hasattr(PromptAuditLog, 'action')
        assert hasattr(PromptAuditLog, 'admin_key_hash')
        assert hasattr(PromptAuditLog, 'timestamp')
        assert hasattr(PromptAuditLog, 'details')
