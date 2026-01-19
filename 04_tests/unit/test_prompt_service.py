"""Unit tests for PromptService.

Tests the service layer for prompt management including:
- CRUD operations
- Version management
- Publish/rollback functionality
"""
import pytest
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from database.connection import Base
from database.models import PromptTemplate, PromptVersion
from services.prompt_service import PromptService, PromptNotFoundError, VersionNotFoundError


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
def prompt_service(db_session):
    """Create a PromptService instance with test database."""
    return PromptService(db_session)


class TestPromptServiceCreate:
    """Tests for creating prompt templates."""

    def test_create_prompt_template_success(self, prompt_service, db_session):
        """Test creating a new prompt template."""
        template = prompt_service.create_template(
            name="test_prompt",
            prompt_type="system",
            content="You are a helpful assistant.",
            description="Main system prompt",
            created_by="admin@test.com",
        )

        assert template.id is not None
        assert template.name == "test_prompt"
        assert template.prompt_type == "system"
        assert template.description == "Main system prompt"
        assert len(template.versions) == 1
        assert template.versions[0].content == "You are a helpful assistant."
        assert template.versions[0].is_active is True
        assert template.versions[0].version_number == 1

    def test_create_prompt_template_creates_active_version(self, prompt_service):
        """Test that creating a template also creates an active version."""
        template = prompt_service.create_template(
            name="new_prompt",
            prompt_type="retrieval",
            content="Context: {context}",
        )

        assert template.active_version is not None
        assert template.active_version.is_active is True

    def test_create_prompt_template_duplicate_name_raises_error(self, prompt_service):
        """Test that duplicate names raise an error."""
        prompt_service.create_template(
            name="unique_name",
            prompt_type="system",
            content="Content 1",
        )

        with pytest.raises(ValueError, match="already exists"):
            prompt_service.create_template(
                name="unique_name",
                prompt_type="system",
                content="Content 2",
            )


class TestPromptServiceRead:
    """Tests for reading prompt templates."""

    def test_get_template_by_id(self, prompt_service):
        """Test getting a template by ID."""
        created = prompt_service.create_template(
            name="get_by_id",
            prompt_type="system",
            content="Content",
        )

        template = prompt_service.get_template(created.id)

        assert template is not None
        assert template.id == created.id
        assert template.name == "get_by_id"

    def test_get_template_not_found_raises_error(self, prompt_service):
        """Test that non-existent ID raises error."""
        with pytest.raises(PromptNotFoundError):
            prompt_service.get_template(9999)

    def test_get_template_by_name(self, prompt_service):
        """Test getting a template by name."""
        prompt_service.create_template(
            name="named_prompt",
            prompt_type="system",
            content="Content",
        )

        template = prompt_service.get_template_by_name("named_prompt")

        assert template is not None
        assert template.name == "named_prompt"

    def test_get_template_by_name_not_found_returns_none(self, prompt_service):
        """Test that non-existent name returns None."""
        result = prompt_service.get_template_by_name("nonexistent")
        assert result is None

    def test_list_templates(self, prompt_service):
        """Test listing all templates."""
        prompt_service.create_template(name="list_1", prompt_type="system", content="C1")
        prompt_service.create_template(name="list_2", prompt_type="retrieval", content="C2")

        templates = prompt_service.list_templates()

        assert len(templates) == 2

    def test_list_templates_filters_deleted(self, prompt_service, db_session):
        """Test that deleted templates are not listed by default."""
        t1 = prompt_service.create_template(name="active", prompt_type="system", content="C1")
        t2 = prompt_service.create_template(name="deleted", prompt_type="system", content="C2")

        t2.deleted_at = datetime.now(timezone.utc)
        db_session.commit()

        templates = prompt_service.list_templates()

        assert len(templates) == 1
        assert templates[0].name == "active"

    def test_list_templates_by_type(self, prompt_service):
        """Test filtering templates by type."""
        prompt_service.create_template(name="sys_1", prompt_type="system", content="C1")
        prompt_service.create_template(name="ret_1", prompt_type="retrieval", content="C2")
        prompt_service.create_template(name="sys_2", prompt_type="system", content="C3")

        templates = prompt_service.list_templates(prompt_type="system")

        assert len(templates) == 2
        assert all(t.prompt_type == "system" for t in templates)


class TestPromptServiceUpdate:
    """Tests for updating prompt templates."""

    def test_update_template_content_creates_new_version(self, prompt_service):
        """Test that updating content creates a new version."""
        template = prompt_service.create_template(
            name="versioned",
            prompt_type="system",
            content="Version 1",
        )

        updated = prompt_service.update_template(
            template_id=template.id,
            content="Version 2",
            created_by="editor@test.com",
        )

        assert len(updated.versions) == 2
        assert updated.active_version.content == "Version 2"
        assert updated.active_version.version_number == 2
        assert updated.active_version.created_by == "editor@test.com"

    def test_update_template_metadata_only(self, prompt_service):
        """Test updating only template metadata without new version."""
        template = prompt_service.create_template(
            name="metadata_test",
            prompt_type="system",
            content="Content",
        )

        updated = prompt_service.update_template(
            template_id=template.id,
            description="Updated description",
        )

        assert updated.description == "Updated description"
        assert len(updated.versions) == 1  # No new version created

    def test_update_template_not_found_raises_error(self, prompt_service):
        """Test that updating non-existent template raises error."""
        with pytest.raises(PromptNotFoundError):
            prompt_service.update_template(
                template_id=9999,
                content="New content",
            )

    def test_update_with_change_notes(self, prompt_service):
        """Test that change notes are stored in version."""
        template = prompt_service.create_template(
            name="notes_test",
            prompt_type="system",
            content="V1",
        )

        updated = prompt_service.update_template(
            template_id=template.id,
            content="V2",
            change_notes="Fixed greeting format",
        )

        assert updated.active_version.change_notes == "Fixed greeting format"


class TestPromptServiceDelete:
    """Tests for deleting prompt templates."""

    def test_delete_template_soft_delete(self, prompt_service):
        """Test that delete performs soft delete."""
        template = prompt_service.create_template(
            name="deletable",
            prompt_type="system",
            content="Content",
        )

        prompt_service.delete_template(template.id)

        # Template should still exist but have deleted_at set
        deleted = prompt_service.get_template(template.id, include_deleted=True)
        assert deleted.deleted_at is not None

    def test_delete_template_not_found_raises_error(self, prompt_service):
        """Test that deleting non-existent template raises error."""
        with pytest.raises(PromptNotFoundError):
            prompt_service.delete_template(9999)


class TestPromptServiceVersionManagement:
    """Tests for version management functionality."""

    def test_get_version_by_number(self, prompt_service):
        """Test getting a specific version by number."""
        template = prompt_service.create_template(
            name="version_test",
            prompt_type="system",
            content="V1",
        )
        prompt_service.update_template(template.id, content="V2")

        version = prompt_service.get_version(template.id, version_number=1)

        assert version.content == "V1"
        assert version.version_number == 1

    def test_get_version_not_found_raises_error(self, prompt_service):
        """Test that non-existent version raises error."""
        template = prompt_service.create_template(
            name="no_version",
            prompt_type="system",
            content="V1",
        )

        with pytest.raises(VersionNotFoundError):
            prompt_service.get_version(template.id, version_number=99)

    def test_list_versions(self, prompt_service):
        """Test listing all versions for a template."""
        template = prompt_service.create_template(
            name="multi_version",
            prompt_type="system",
            content="V1",
        )
        prompt_service.update_template(template.id, content="V2")
        prompt_service.update_template(template.id, content="V3")

        versions = prompt_service.list_versions(template.id)

        assert len(versions) == 3

    def test_get_active_content(self, prompt_service):
        """Test getting active prompt content by template name."""
        prompt_service.create_template(
            name="active_content_test",
            prompt_type="system",
            content="Active prompt content",
        )

        content = prompt_service.get_active_content("active_content_test")

        assert content == "Active prompt content"

    def test_get_active_content_not_found_returns_none(self, prompt_service):
        """Test that non-existent template returns None."""
        result = prompt_service.get_active_content("nonexistent")
        assert result is None


class TestPromptServicePublishRollback:
    """Tests for publish and rollback functionality."""

    def test_publish_version_activates_version(self, prompt_service):
        """Test that publishing a version activates it."""
        template = prompt_service.create_template(
            name="publish_test",
            prompt_type="system",
            content="V1",
        )
        prompt_service.update_template(template.id, content="V2")

        # V2 should be active after update
        # Publish V1
        prompt_service.publish_version(template.id, version_number=1)

        refreshed = prompt_service.get_template(template.id)
        assert refreshed.active_version.version_number == 1

    def test_publish_version_deactivates_previous(self, prompt_service, db_session):
        """Test that publishing deactivates the previous active version."""
        template = prompt_service.create_template(
            name="deactivate_test",
            prompt_type="system",
            content="V1",
        )
        prompt_service.update_template(template.id, content="V2")

        prompt_service.publish_version(template.id, version_number=1)

        # Count active versions
        active_count = db_session.query(PromptVersion).filter(
            PromptVersion.template_id == template.id,
            PromptVersion.is_active == True,
        ).count()

        assert active_count == 1

    def test_rollback_to_previous_version(self, prompt_service):
        """Test rolling back to the previous version."""
        template = prompt_service.create_template(
            name="rollback_test",
            prompt_type="system",
            content="V1",
        )
        prompt_service.update_template(template.id, content="V2")
        prompt_service.update_template(template.id, content="V3")

        # V3 is active, rollback to V2
        prompt_service.rollback(template.id)

        refreshed = prompt_service.get_template(template.id)
        assert refreshed.active_version.version_number == 2

    def test_rollback_from_v1_raises_error(self, prompt_service):
        """Test that rolling back from V1 raises error."""
        template = prompt_service.create_template(
            name="v1_rollback",
            prompt_type="system",
            content="V1",
        )

        with pytest.raises(ValueError, match="Cannot rollback"):
            prompt_service.rollback(template.id)
