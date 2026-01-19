"""Integration tests for default prompt seeding.

Tests that default prompts are correctly seeded on fresh install.
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from database.connection import Base
from database.models import PromptTemplate, PromptVersion
from database.seeds.prompts import seed_default_prompts


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


class TestPromptSeeding:
    """Tests for default prompt seeding."""

    def test_seed_default_prompts_creates_templates(self, db_session):
        """Test that seeding creates prompt templates."""
        seed_default_prompts(db_session)

        templates = db_session.query(PromptTemplate).all()
        assert len(templates) > 0

    def test_seed_default_prompts_creates_system_prompt(self, db_session):
        """Test that system prompt is created."""
        seed_default_prompts(db_session)

        system_prompt = db_session.query(PromptTemplate).filter(
            PromptTemplate.name == "system_prompt"
        ).first()

        assert system_prompt is not None
        assert system_prompt.prompt_type == "system"
        assert system_prompt.description is not None

    def test_seed_default_prompts_creates_active_versions(self, db_session):
        """Test that seeded prompts have active versions."""
        seed_default_prompts(db_session)

        templates = db_session.query(PromptTemplate).all()

        for template in templates:
            active_version = db_session.query(PromptVersion).filter(
                PromptVersion.template_id == template.id,
                PromptVersion.is_active == True,
            ).first()

            assert active_version is not None
            assert active_version.content is not None
            assert len(active_version.content) > 0

    def test_seed_default_prompts_idempotent(self, db_session):
        """Test that seeding is idempotent (can be run multiple times)."""
        seed_default_prompts(db_session)
        count_first = db_session.query(PromptTemplate).count()

        seed_default_prompts(db_session)
        count_second = db_session.query(PromptTemplate).count()

        assert count_first == count_second

    def test_seed_creates_retrieval_prompt(self, db_session):
        """Test that retrieval prompt is created."""
        seed_default_prompts(db_session)

        retrieval_prompt = db_session.query(PromptTemplate).filter(
            PromptTemplate.name == "retrieval_prompt"
        ).first()

        assert retrieval_prompt is not None
        assert retrieval_prompt.prompt_type == "retrieval"

    def test_seed_prompt_content_not_empty(self, db_session):
        """Test that seeded prompts have non-empty content."""
        seed_default_prompts(db_session)

        versions = db_session.query(PromptVersion).all()

        for version in versions:
            assert version.content is not None
            assert len(version.content.strip()) > 50  # Meaningful content

    def test_seed_marks_created_by_system(self, db_session):
        """Test that seeded versions are marked as system-created."""
        seed_default_prompts(db_session)

        versions = db_session.query(PromptVersion).all()

        for version in versions:
            assert version.created_by == "system"
