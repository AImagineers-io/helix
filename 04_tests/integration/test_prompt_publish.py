"""Integration tests for prompt publish and rollback endpoints.

Tests version management endpoints:
- POST /prompts/{id}/publish - Activate a specific version
- POST /prompts/{id}/rollback - Rollback to previous version
"""
import pytest
from fastapi import Header
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from database.connection import Base, get_db
from database.models import PromptTemplate, PromptVersion
from api.main import create_app
from api.auth import verify_api_key
from core.config import Settings


@pytest.fixture
def db_session():
    """Create an in-memory SQLite database for testing."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def test_settings():
    """Create test settings with API key."""
    return Settings(api_key="test-api-key")


@pytest.fixture
def client(db_session, test_settings):
    """Create test client with database override."""
    app = create_app(test_settings)

    # Override get_db dependency
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    # Override API key verification
    def override_verify_api_key(x_api_key: str | None = Header(default=None, alias="X-API-Key")):
        from fastapi import HTTPException
        if not x_api_key:
            raise HTTPException(status_code=401, detail="API key required")
        if x_api_key != "test-api-key":
            raise HTTPException(status_code=401, detail="Invalid API key")
        return x_api_key

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[verify_api_key] = override_verify_api_key

    return TestClient(app)


@pytest.fixture
def auth_headers():
    """Authentication headers with API key."""
    return {"X-API-Key": "test-api-key"}


@pytest.fixture
def template_with_versions(db_session):
    """Create a template with multiple versions for testing."""
    template = PromptTemplate(name="versioned_template", prompt_type="system")
    db_session.add(template)
    db_session.flush()

    v1 = PromptVersion(
        template_id=template.id,
        content="Version 1",
        version_number=1,
        is_active=False,
    )
    v2 = PromptVersion(
        template_id=template.id,
        content="Version 2",
        version_number=2,
        is_active=False,
    )
    v3 = PromptVersion(
        template_id=template.id,
        content="Version 3",
        version_number=3,
        is_active=True,
    )
    db_session.add_all([v1, v2, v3])
    db_session.commit()

    return template


class TestPublishEndpoint:
    """Tests for POST /prompts/{id}/publish endpoint."""

    def test_publish_version_success(self, client, auth_headers, template_with_versions):
        """Test publishing a specific version."""
        payload = {"version_number": 2}

        response = client.post(
            f"/prompts/{template_with_versions.id}/publish",
            json=payload,
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["version_number"] == 2
        assert data["is_active"] is True

    def test_publish_version_deactivates_previous(
        self, client, auth_headers, template_with_versions, db_session
    ):
        """Test that publishing deactivates the current active version."""
        payload = {"version_number": 1}

        response = client.post(
            f"/prompts/{template_with_versions.id}/publish",
            json=payload,
            headers=auth_headers,
        )

        assert response.status_code == 200

        # Verify only one active version
        active_versions = db_session.query(PromptVersion).filter(
            PromptVersion.template_id == template_with_versions.id,
            PromptVersion.is_active == True,
        ).all()

        assert len(active_versions) == 1
        assert active_versions[0].version_number == 1

    def test_publish_nonexistent_version_returns_404(
        self, client, auth_headers, template_with_versions
    ):
        """Test publishing non-existent version returns 404."""
        payload = {"version_number": 99}

        response = client.post(
            f"/prompts/{template_with_versions.id}/publish",
            json=payload,
            headers=auth_headers,
        )

        assert response.status_code == 404

    def test_publish_nonexistent_template_returns_404(self, client, auth_headers):
        """Test publishing version for non-existent template returns 404."""
        payload = {"version_number": 1}

        response = client.post(
            "/prompts/9999/publish",
            json=payload,
            headers=auth_headers,
        )

        assert response.status_code == 404

    def test_publish_requires_auth(self, client, template_with_versions):
        """Test that publishing requires API key."""
        payload = {"version_number": 1}

        response = client.post(
            f"/prompts/{template_with_versions.id}/publish",
            json=payload,
        )

        assert response.status_code == 401


class TestRollbackEndpoint:
    """Tests for POST /prompts/{id}/rollback endpoint."""

    def test_rollback_to_previous_version(
        self, client, auth_headers, template_with_versions
    ):
        """Test rolling back to the previous version."""
        # V3 is currently active, rollback should activate V2
        response = client.post(
            f"/prompts/{template_with_versions.id}/rollback",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["version_number"] == 2
        assert data["is_active"] is True

    def test_rollback_updates_active_version(
        self, client, auth_headers, template_with_versions, db_session
    ):
        """Test that rollback properly updates which version is active."""
        response = client.post(
            f"/prompts/{template_with_versions.id}/rollback",
            headers=auth_headers,
        )

        assert response.status_code == 200

        # Verify V2 is now active
        v2 = db_session.query(PromptVersion).filter(
            PromptVersion.template_id == template_with_versions.id,
            PromptVersion.version_number == 2,
        ).first()

        assert v2.is_active is True

        # Verify V3 is no longer active
        v3 = db_session.query(PromptVersion).filter(
            PromptVersion.template_id == template_with_versions.id,
            PromptVersion.version_number == 3,
        ).first()

        assert v3.is_active is False

    def test_rollback_from_v1_returns_400(self, client, auth_headers, db_session):
        """Test that rolling back from V1 returns error."""
        template = PromptTemplate(name="v1_template", prompt_type="system")
        db_session.add(template)
        db_session.flush()

        v1 = PromptVersion(
            template_id=template.id,
            content="Version 1",
            version_number=1,
            is_active=True,
        )
        db_session.add(v1)
        db_session.commit()

        response = client.post(
            f"/prompts/{template.id}/rollback",
            headers=auth_headers,
        )

        assert response.status_code == 400
        assert "Cannot rollback" in response.json()["detail"]

    def test_rollback_nonexistent_template_returns_404(self, client, auth_headers):
        """Test rolling back non-existent template returns 404."""
        response = client.post(
            "/prompts/9999/rollback",
            headers=auth_headers,
        )

        assert response.status_code == 404

    def test_rollback_requires_auth(self, client, template_with_versions):
        """Test that rollback requires API key."""
        response = client.post(
            f"/prompts/{template_with_versions.id}/rollback",
        )

        assert response.status_code == 401
