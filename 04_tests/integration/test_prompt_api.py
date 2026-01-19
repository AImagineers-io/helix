"""Integration tests for Prompt Management API.

Tests the REST API endpoints for managing prompt templates:
- GET /prompts - List all templates
- POST /prompts - Create template
- GET /prompts/{id} - Get template details with versions
- PUT /prompts/{id} - Update template content (creates new version)
- DELETE /prompts/{id} - Soft delete template
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


class TestPromptListAPI:
    """Tests for GET /prompts endpoint."""

    def test_list_prompts_empty(self, client, auth_headers):
        """Test listing prompts when none exist."""
        response = client.get("/prompts", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    def test_list_prompts_returns_templates(self, client, auth_headers, db_session):
        """Test listing prompts returns all templates."""
        # Create test templates
        t1 = PromptTemplate(name="system_prompt", prompt_type="system")
        t2 = PromptTemplate(name="retrieval_prompt", prompt_type="retrieval")
        db_session.add_all([t1, t2])
        db_session.commit()

        response = client.get("/prompts", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["name"] in ["system_prompt", "retrieval_prompt"]

    def test_list_prompts_filters_by_type(self, client, auth_headers, db_session):
        """Test filtering prompts by type."""
        t1 = PromptTemplate(name="sys1", prompt_type="system")
        t2 = PromptTemplate(name="ret1", prompt_type="retrieval")
        db_session.add_all([t1, t2])
        db_session.commit()

        response = client.get("/prompts?prompt_type=system", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["prompt_type"] == "system"

    def test_list_prompts_requires_auth(self, client):
        """Test that listing prompts requires API key."""
        response = client.get("/prompts")
        assert response.status_code == 401


class TestPromptCreateAPI:
    """Tests for POST /prompts endpoint."""

    def test_create_prompt_success(self, client, auth_headers):
        """Test creating a new prompt template."""
        payload = {
            "name": "new_prompt",
            "prompt_type": "system",
            "content": "You are a helpful assistant.",
            "description": "Main system prompt",
            "created_by": "admin@test.com",
        }

        response = client.post("/prompts", json=payload, headers=auth_headers)

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "new_prompt"
        assert data["prompt_type"] == "system"
        assert data["description"] == "Main system prompt"
        assert "id" in data
        assert "created_at" in data

    def test_create_prompt_duplicate_name_fails(self, client, auth_headers, db_session):
        """Test that duplicate names are rejected."""
        t1 = PromptTemplate(name="existing", prompt_type="system")
        db_session.add(t1)
        db_session.commit()

        payload = {
            "name": "existing",
            "prompt_type": "system",
            "content": "Content",
        }

        response = client.post("/prompts", json=payload, headers=auth_headers)

        assert response.status_code == 400
        assert "already exists" in response.json()["detail"].lower()

    def test_create_prompt_missing_required_fields(self, client, auth_headers):
        """Test that missing required fields returns 422."""
        payload = {"name": "incomplete"}

        response = client.post("/prompts", json=payload, headers=auth_headers)

        assert response.status_code == 422

    def test_create_prompt_requires_auth(self, client):
        """Test that creating prompts requires API key."""
        payload = {"name": "test", "prompt_type": "system", "content": "Test"}
        response = client.post("/prompts", json=payload)
        assert response.status_code == 401


class TestPromptGetAPI:
    """Tests for GET /prompts/{id} endpoint."""

    def test_get_prompt_by_id(self, client, auth_headers, db_session):
        """Test getting a prompt by ID includes versions."""
        template = PromptTemplate(name="test", prompt_type="system")
        db_session.add(template)
        db_session.flush()

        version = PromptVersion(
            template_id=template.id,
            content="Test content",
            version_number=1,
            is_active=True,
        )
        db_session.add(version)
        db_session.commit()

        response = client.get(f"/prompts/{template.id}", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == template.id
        assert data["name"] == "test"
        assert "versions" in data
        assert len(data["versions"]) == 1
        assert data["versions"][0]["content"] == "Test content"

    def test_get_prompt_not_found(self, client, auth_headers):
        """Test getting non-existent prompt returns 404."""
        response = client.get("/prompts/9999", headers=auth_headers)
        assert response.status_code == 404

    def test_get_prompt_requires_auth(self, client, db_session):
        """Test that getting prompt requires API key."""
        template = PromptTemplate(name="test", prompt_type="system")
        db_session.add(template)
        db_session.commit()

        response = client.get(f"/prompts/{template.id}")
        assert response.status_code == 401


class TestPromptUpdateAPI:
    """Tests for PUT /prompts/{id} endpoint."""

    def test_update_prompt_content(self, client, auth_headers, db_session):
        """Test updating prompt content creates new version."""
        template = PromptTemplate(name="update_test", prompt_type="system")
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

        payload = {
            "content": "Version 2",
            "created_by": "editor@test.com",
            "change_notes": "Updated greeting",
        }

        response = client.put(
            f"/prompts/{template.id}",
            json=payload,
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["versions"]) == 2

    def test_update_prompt_metadata_only(self, client, auth_headers, db_session):
        """Test updating only metadata doesn't create version."""
        template = PromptTemplate(name="metadata_test", prompt_type="system")
        db_session.add(template)
        db_session.flush()

        v1 = PromptVersion(
            template_id=template.id,
            content="Content",
            version_number=1,
            is_active=True,
        )
        db_session.add(v1)
        db_session.commit()

        payload = {"description": "Updated description"}

        response = client.put(
            f"/prompts/{template.id}",
            json=payload,
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["description"] == "Updated description"
        assert len(data["versions"]) == 1

    def test_update_prompt_not_found(self, client, auth_headers):
        """Test updating non-existent prompt returns 404."""
        payload = {"content": "New content"}
        response = client.put("/prompts/9999", json=payload, headers=auth_headers)
        assert response.status_code == 404

    def test_update_prompt_requires_auth(self, client, db_session):
        """Test that updating prompt requires API key."""
        template = PromptTemplate(name="test", prompt_type="system")
        db_session.add(template)
        db_session.commit()

        payload = {"content": "New"}
        response = client.put(f"/prompts/{template.id}", json=payload)
        assert response.status_code == 401


class TestPromptDeleteAPI:
    """Tests for DELETE /prompts/{id} endpoint."""

    def test_delete_prompt_success(self, client, auth_headers, db_session):
        """Test deleting a prompt (soft delete)."""
        template = PromptTemplate(name="deletable", prompt_type="system")
        db_session.add(template)
        db_session.commit()

        response = client.delete(f"/prompts/{template.id}", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Prompt template deleted successfully"

        # Verify soft delete
        db_session.refresh(template)
        assert template.deleted_at is not None

    def test_delete_prompt_not_found(self, client, auth_headers):
        """Test deleting non-existent prompt returns 404."""
        response = client.delete("/prompts/9999", headers=auth_headers)
        assert response.status_code == 404

    def test_delete_prompt_requires_auth(self, client, db_session):
        """Test that deleting prompt requires API key."""
        template = PromptTemplate(name="test", prompt_type="system")
        db_session.add(template)
        db_session.commit()

        response = client.delete(f"/prompts/{template.id}")
        assert response.status_code == 401
