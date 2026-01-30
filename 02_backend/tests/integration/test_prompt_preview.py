"""
Integration tests for prompt preview endpoint.

Tests that prompt content can be previewed with sample context variables.
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


class TestPromptPreview:
    """Test suite for prompt preview endpoint."""

    def test_preview_renders_template_variables(self, client, auth_headers):
        """Test that preview substitutes template variables."""
        # Arrange: Create a prompt with variables
        create_response = client.post(
            "/prompts",
            json={
                "name": "test_prompt",
                "prompt_type": "system_prompt",
                "content": "Hello {user_name}, your order {order_id} is ready."
            },
            headers=auth_headers
        )
        assert create_response.status_code == 201
        template_id = create_response.json()["id"]

        # Act: Preview with context
        preview_response = client.post(
            f"/prompts/{template_id}/preview",
            json={
                "context": {
                    "user_name": "John",
                    "order_id": "12345"
                }
            },
            headers=auth_headers
        )

        # Assert
        assert preview_response.status_code == 200
        result = preview_response.json()
        assert result["rendered"] == "Hello John, your order 12345 is ready."

    def test_preview_returns_original_if_no_variables(self, client, auth_headers):
        """Test that preview returns original content if no variables."""
        # Arrange: Create a prompt without variables
        create_response = client.post(
            "/prompts",
            json={
                "name": "test_prompt",
                "prompt_type": "system_prompt",
                "content": "Static content without variables."
            },
            headers=auth_headers
        )
        assert create_response.status_code == 201
        template_id = create_response.json()["id"]

        # Act: Preview with empty context
        preview_response = client.post(
            f"/prompts/{template_id}/preview",
            json={"context": {}},
            headers=auth_headers
        )

        # Assert
        assert preview_response.status_code == 200
        assert preview_response.json()["rendered"] == "Static content without variables."

    def test_preview_preserves_unmatched_variables(self, client, auth_headers):
        """Test that unmatched variables are preserved in output."""
        # Arrange: Create a prompt with variables
        create_response = client.post(
            "/prompts",
            json={
                "name": "test_prompt",
                "prompt_type": "system_prompt",
                "content": "Hello {user_name}, your code is {code}."
            },
            headers=auth_headers
        )
        assert create_response.status_code == 201
        template_id = create_response.json()["id"]

        # Act: Preview with partial context
        preview_response = client.post(
            f"/prompts/{template_id}/preview",
            json={
                "context": {"user_name": "Alice"}
            },
            headers=auth_headers
        )

        # Assert: code variable should be preserved
        assert preview_response.status_code == 200
        assert preview_response.json()["rendered"] == "Hello Alice, your code is {code}."

    def test_preview_returns_404_for_missing_template(self, client, auth_headers):
        """Test that preview returns 404 for non-existent template."""
        # Act
        preview_response = client.post(
            "/prompts/99999/preview",
            json={"context": {}},
            headers=auth_headers
        )

        # Assert
        assert preview_response.status_code == 404

    def test_preview_uses_active_version(self, client, auth_headers):
        """Test that preview uses the active version content."""
        # Arrange: Create prompt
        create_response = client.post(
            "/prompts",
            json={
                "name": "test_prompt",
                "prompt_type": "system_prompt",
                "content": "Version 1: Hello {name}"
            },
            headers=auth_headers
        )
        template = create_response.json()
        template_id = template["id"]

        # Update to create version 2
        client.put(
            f"/prompts/{template_id}",
            json={
                "content": "Version 2: Hi {name}",
                "edit_version": template["edit_version"]
            },
            headers=auth_headers
        )

        # Act: Preview
        preview_response = client.post(
            f"/prompts/{template_id}/preview",
            json={"context": {"name": "Bob"}},
            headers=auth_headers
        )

        # Assert: Should use version 2 (active)
        assert preview_response.status_code == 200
        assert preview_response.json()["rendered"] == "Version 2: Hi Bob"

    def test_preview_returns_original_content_in_response(self, client, auth_headers):
        """Test that preview also returns original content for comparison."""
        # Arrange
        create_response = client.post(
            "/prompts",
            json={
                "name": "test_prompt",
                "prompt_type": "system_prompt",
                "content": "Hello {name}"
            },
            headers=auth_headers
        )
        template_id = create_response.json()["id"]

        # Act
        preview_response = client.post(
            f"/prompts/{template_id}/preview",
            json={"context": {"name": "Test"}},
            headers=auth_headers
        )

        # Assert
        assert preview_response.status_code == 200
        result = preview_response.json()
        assert "original" in result
        assert result["original"] == "Hello {name}"
        assert result["rendered"] == "Hello Test"

    def test_preview_lists_variables_found(self, client, auth_headers):
        """Test that preview lists variables found in template."""
        # Arrange
        create_response = client.post(
            "/prompts",
            json={
                "name": "test_prompt",
                "prompt_type": "system_prompt",
                "content": "Hello {user_name}, your {item_type} {item_id} is ready."
            },
            headers=auth_headers
        )
        template_id = create_response.json()["id"]

        # Act
        preview_response = client.post(
            f"/prompts/{template_id}/preview",
            json={"context": {}},
            headers=auth_headers
        )

        # Assert
        assert preview_response.status_code == 200
        result = preview_response.json()
        assert "variables" in result
        assert set(result["variables"]) == {"user_name", "item_type", "item_id"}

    def test_preview_can_specify_version_number(self, client, auth_headers):
        """Test that preview can render a specific version."""
        # Arrange: Create prompt with two versions
        create_response = client.post(
            "/prompts",
            json={
                "name": "test_prompt",
                "prompt_type": "system_prompt",
                "content": "Version 1: {message}"
            },
            headers=auth_headers
        )
        template = create_response.json()
        template_id = template["id"]

        # Update to create version 2
        client.put(
            f"/prompts/{template_id}",
            json={
                "content": "Version 2: {message}",
                "edit_version": template["edit_version"]
            },
            headers=auth_headers
        )

        # Act: Preview version 1 specifically
        preview_response = client.post(
            f"/prompts/{template_id}/preview",
            json={
                "context": {"message": "test"},
                "version_number": 1
            },
            headers=auth_headers
        )

        # Assert: Should render version 1
        assert preview_response.status_code == 200
        assert preview_response.json()["rendered"] == "Version 1: test"
