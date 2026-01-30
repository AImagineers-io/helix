"""
Integration tests for prompt optimistic locking.

Tests that concurrent edits are handled with optimistic locking.
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


class TestOptimisticLocking:
    """Test suite for optimistic locking on prompt updates."""

    def test_update_prompt_requires_edit_version(self, client, auth_headers):
        """Test that update request must include edit_version."""
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
        assert create_response.status_code == 201
        template_id = create_response.json()["id"]

        # Act: Try to update without edit_version
        update_response = client.put(
            f"/prompts/{template_id}",
            json={"content": "Updated content"},
            headers=auth_headers
        )

        # Assert: Should fail (400 Bad Request)
        assert update_response.status_code == 400
        assert "edit_version" in update_response.json()["detail"].lower()

    def test_update_prompt_with_correct_version_succeeds(self, client, auth_headers):
        """Test that update succeeds with correct edit_version."""
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
        assert create_response.status_code == 201
        template = create_response.json()
        template_id = template["id"]
        edit_version = template["edit_version"]

        # Act: Update with correct version
        update_response = client.put(
            f"/prompts/{template_id}",
            json={
                "content": "Updated content",
                "edit_version": edit_version
            },
            headers=auth_headers
        )

        # Assert: Should succeed
        assert update_response.status_code == 200
        assert update_response.json()["edit_version"] == edit_version + 1

    def test_update_prompt_with_wrong_version_returns_409(self, client, auth_headers):
        """Test that update with wrong edit_version returns 409 Conflict."""
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
        assert create_response.status_code == 201
        template = create_response.json()
        template_id = template["id"]

        # Act: Try to update with wrong version (outdated)
        update_response = client.put(
            f"/prompts/{template_id}",
            json={
                "content": "Updated content",
                "edit_version": 999  # Wrong version
            },
            headers=auth_headers
        )

        # Assert: Should return 409 Conflict
        assert update_response.status_code == 409
        assert "conflict" in update_response.json()["detail"].lower()

    def test_concurrent_updates_second_fails(self, client, auth_headers):
        """Test that second concurrent update fails with 409."""
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
        assert create_response.status_code == 201
        template = create_response.json()
        template_id = template["id"]
        original_version = template["edit_version"]

        # Act: First update succeeds
        first_update = client.put(
            f"/prompts/{template_id}",
            json={
                "content": "First update",
                "edit_version": original_version
            },
            headers=auth_headers
        )
        assert first_update.status_code == 200

        # Act: Second update with same original version fails
        second_update = client.put(
            f"/prompts/{template_id}",
            json={
                "content": "Second update",
                "edit_version": original_version  # Stale version
            },
            headers=auth_headers
        )

        # Assert: Should return 409 Conflict
        assert second_update.status_code == 409

    def test_get_prompt_returns_edit_version(self, client, auth_headers):
        """Test that GET endpoint returns edit_version field."""
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
        assert create_response.status_code == 201
        template_id = create_response.json()["id"]

        # Act: Get the prompt
        get_response = client.get(
            f"/prompts/{template_id}",
            headers=auth_headers
        )

        # Assert: Should include edit_version
        assert get_response.status_code == 200
        assert "edit_version" in get_response.json()
        assert get_response.json()["edit_version"] >= 1

    def test_edit_version_increments_on_each_update(self, client, auth_headers):
        """Test that edit_version increments with each successful update."""
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
        version = template["edit_version"]

        # Act: Multiple updates
        for i in range(3):
            update_response = client.put(
                f"/prompts/{template_id}",
                json={
                    "content": f"Update {i}",
                    "edit_version": version
                },
                headers=auth_headers
            )
            assert update_response.status_code == 200
            version = update_response.json()["edit_version"]

        # Assert: Version should have incremented 3 times
        assert version == template["edit_version"] + 3

    def test_metadata_update_also_requires_version(self, client, auth_headers):
        """Test that metadata-only updates also require edit_version."""
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

        # Act: Try metadata update without version
        update_response = client.put(
            f"/prompts/{template_id}",
            json={"description": "New description"},
            headers=auth_headers
        )

        # Assert: Should fail
        assert update_response.status_code == 400

    def test_list_prompts_includes_edit_version(self, client, auth_headers):
        """Test that list endpoint includes edit_version for each template."""
        # Arrange: Create prompts
        for i in range(2):
            client.post(
                "/prompts",
                json={
                    "name": f"test_prompt_{i}",
                    "prompt_type": "system_prompt",
                    "content": f"Content {i}"
                },
                headers=auth_headers
            )

        # Act: List prompts
        list_response = client.get("/prompts", headers=auth_headers)

        # Assert: Each should have edit_version
        assert list_response.status_code == 200
        for template in list_response.json():
            assert "edit_version" in template
