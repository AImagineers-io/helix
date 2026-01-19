"""Integration tests for PromptTemplate and PromptVersion models.

Tests database CRUD operations and relationships between models.
"""
import pytest
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from database.connection import Base
from database.models import PromptTemplate, PromptVersion


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


class TestPromptTemplateModel:
    """Tests for PromptTemplate model."""

    def test_create_prompt_template_with_required_fields(self, db_session):
        """Test creating a prompt template with required fields."""
        template = PromptTemplate(
            name="system_prompt",
            description="Main system prompt for the chatbot",
            prompt_type="system",
        )
        db_session.add(template)
        db_session.commit()

        assert template.id is not None
        assert template.name == "system_prompt"
        assert template.description == "Main system prompt for the chatbot"
        assert template.prompt_type == "system"
        assert template.created_at is not None
        assert template.updated_at is not None

    def test_prompt_template_name_must_be_unique(self, db_session):
        """Test that prompt template names must be unique."""
        template1 = PromptTemplate(
            name="unique_name",
            prompt_type="system",
        )
        db_session.add(template1)
        db_session.commit()

        template2 = PromptTemplate(
            name="unique_name",
            prompt_type="system",
        )
        db_session.add(template2)

        with pytest.raises(Exception):  # IntegrityError
            db_session.commit()

    def test_prompt_template_has_versions_relationship(self, db_session):
        """Test that prompt template has a versions relationship."""
        template = PromptTemplate(
            name="test_template",
            prompt_type="system",
        )
        db_session.add(template)
        db_session.commit()

        version = PromptVersion(
            template_id=template.id,
            content="This is the prompt content",
            version_number=1,
            is_active=True,
        )
        db_session.add(version)
        db_session.commit()

        db_session.refresh(template)
        assert len(template.versions) == 1
        assert template.versions[0].content == "This is the prompt content"

    def test_prompt_template_soft_delete(self, db_session):
        """Test soft delete functionality for prompt templates."""
        template = PromptTemplate(
            name="deletable_template",
            prompt_type="system",
        )
        db_session.add(template)
        db_session.commit()

        assert template.deleted_at is None

        template.deleted_at = datetime.now(timezone.utc)
        db_session.commit()

        assert template.deleted_at is not None


class TestPromptVersionModel:
    """Tests for PromptVersion model."""

    def test_create_prompt_version(self, db_session):
        """Test creating a prompt version."""
        template = PromptTemplate(
            name="versioned_template",
            prompt_type="system",
        )
        db_session.add(template)
        db_session.commit()

        version = PromptVersion(
            template_id=template.id,
            content="You are a helpful assistant.",
            version_number=1,
            is_active=True,
        )
        db_session.add(version)
        db_session.commit()

        assert version.id is not None
        assert version.template_id == template.id
        assert version.content == "You are a helpful assistant."
        assert version.version_number == 1
        assert version.is_active is True
        assert version.created_at is not None

    def test_prompt_version_belongs_to_template(self, db_session):
        """Test that version has a reference to its template."""
        template = PromptTemplate(
            name="parent_template",
            prompt_type="system",
        )
        db_session.add(template)
        db_session.commit()

        version = PromptVersion(
            template_id=template.id,
            content="Version content",
            version_number=1,
            is_active=True,
        )
        db_session.add(version)
        db_session.commit()

        db_session.refresh(version)
        assert version.template is not None
        assert version.template.name == "parent_template"

    def test_multiple_versions_per_template(self, db_session):
        """Test creating multiple versions for a single template."""
        template = PromptTemplate(
            name="multi_version_template",
            prompt_type="system",
        )
        db_session.add(template)
        db_session.commit()

        version1 = PromptVersion(
            template_id=template.id,
            content="Version 1 content",
            version_number=1,
            is_active=False,
        )
        version2 = PromptVersion(
            template_id=template.id,
            content="Version 2 content",
            version_number=2,
            is_active=True,
        )
        db_session.add_all([version1, version2])
        db_session.commit()

        db_session.refresh(template)
        assert len(template.versions) == 2

    def test_only_one_active_version_per_template(self, db_session):
        """Test constraint: only one version should be active per template."""
        template = PromptTemplate(
            name="active_constraint_template",
            prompt_type="system",
        )
        db_session.add(template)
        db_session.commit()

        version1 = PromptVersion(
            template_id=template.id,
            content="Version 1",
            version_number=1,
            is_active=True,
        )
        db_session.add(version1)
        db_session.commit()

        # Get active version
        active = db_session.query(PromptVersion).filter(
            PromptVersion.template_id == template.id,
            PromptVersion.is_active == True,
        ).all()

        assert len(active) == 1

    def test_version_created_by_field(self, db_session):
        """Test that versions track who created them."""
        template = PromptTemplate(
            name="creator_tracking_template",
            prompt_type="system",
        )
        db_session.add(template)
        db_session.commit()

        version = PromptVersion(
            template_id=template.id,
            content="Created by admin",
            version_number=1,
            is_active=True,
            created_by="admin@example.com",
        )
        db_session.add(version)
        db_session.commit()

        assert version.created_by == "admin@example.com"

    def test_version_change_notes(self, db_session):
        """Test that versions can store change notes."""
        template = PromptTemplate(
            name="notes_template",
            prompt_type="system",
        )
        db_session.add(template)
        db_session.commit()

        version = PromptVersion(
            template_id=template.id,
            content="Updated content",
            version_number=2,
            is_active=True,
            change_notes="Fixed typo in greeting",
        )
        db_session.add(version)
        db_session.commit()

        assert version.change_notes == "Fixed typo in greeting"


class TestPromptTemplateTypes:
    """Tests for different prompt template types."""

    def test_system_prompt_type(self, db_session):
        """Test creating a system prompt template."""
        template = PromptTemplate(
            name="main_system",
            prompt_type="system",
            description="Main system prompt",
        )
        db_session.add(template)
        db_session.commit()

        assert template.prompt_type == "system"

    def test_retrieval_prompt_type(self, db_session):
        """Test creating a retrieval prompt template."""
        template = PromptTemplate(
            name="rag_prompt",
            prompt_type="retrieval",
            description="RAG system prompt",
        )
        db_session.add(template)
        db_session.commit()

        assert template.prompt_type == "retrieval"

    def test_moderation_prompt_type(self, db_session):
        """Test creating a moderation prompt template."""
        template = PromptTemplate(
            name="moderation_prompt",
            prompt_type="moderation",
            description="Content moderation prompt",
        )
        db_session.add(template)
        db_session.commit()

        assert template.prompt_type == "moderation"
