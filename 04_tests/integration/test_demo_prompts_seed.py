"""Integration tests for demo prompt seeding.

Tests that demo prompts are correctly seeded for demo instances.
Demo prompts should be generic and helpful, not domain-specific.
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from database.connection import Base
from database.models import PromptTemplate, PromptVersion
from database.seeds.demo_prompts import seed_demo_prompts


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


class TestDemoPromptSeeding:
    """Tests for demo prompt seeding."""

    def test_seed_demo_prompts_creates_templates(self, db_session):
        """Test that seeding creates demo prompt templates."""
        seed_demo_prompts(db_session)

        templates = db_session.query(PromptTemplate).all()
        assert len(templates) > 0

    def test_seed_demo_prompts_creates_demo_system_prompt(self, db_session):
        """Test that demo system prompt is created."""
        seed_demo_prompts(db_session)

        demo_system = db_session.query(PromptTemplate).filter(
            PromptTemplate.name == "demo_system_prompt"
        ).first()

        assert demo_system is not None
        assert demo_system.prompt_type == "system"
        assert demo_system.description is not None

    def test_seed_demo_prompts_creates_demo_retrieval_prompt(self, db_session):
        """Test that demo retrieval prompt is created."""
        seed_demo_prompts(db_session)

        demo_retrieval = db_session.query(PromptTemplate).filter(
            PromptTemplate.name == "demo_retrieval_prompt"
        ).first()

        assert demo_retrieval is not None
        assert demo_retrieval.prompt_type == "retrieval"

    def test_seed_demo_prompts_creates_active_versions(self, db_session):
        """Test that seeded demo prompts have active versions."""
        seed_demo_prompts(db_session)

        templates = db_session.query(PromptTemplate).all()

        for template in templates:
            active_version = db_session.query(PromptVersion).filter(
                PromptVersion.template_id == template.id,
                PromptVersion.is_active == True,
            ).first()

            assert active_version is not None
            assert active_version.content is not None
            assert len(active_version.content) > 0

    def test_seed_demo_prompts_idempotent(self, db_session):
        """Test that demo seeding is idempotent (can be run multiple times)."""
        seed_demo_prompts(db_session)
        count_first = db_session.query(PromptTemplate).count()

        seed_demo_prompts(db_session)
        count_second = db_session.query(PromptTemplate).count()

        assert count_first == count_second

    def test_seed_demo_prompt_content_not_empty(self, db_session):
        """Test that seeded demo prompts have non-empty content."""
        seed_demo_prompts(db_session)

        versions = db_session.query(PromptVersion).all()

        for version in versions:
            assert version.content is not None
            assert len(version.content.strip()) > 50  # Meaningful content

    def test_seed_demo_marks_created_by_system(self, db_session):
        """Test that seeded demo versions are marked as system-created."""
        seed_demo_prompts(db_session)

        versions = db_session.query(PromptVersion).all()

        for version in versions:
            assert version.created_by == "demo_seed"

    def test_seed_demo_prompts_are_generic(self, db_session):
        """Test that demo prompts contain no domain-specific content."""
        seed_demo_prompts(db_session)

        # Domain-specific terms that should NOT appear in demo prompts
        forbidden_terms = [
            "rice", "philrice", "agriculture", "farming",
            "palai", "palay", "variety", "seed", "harvest",
            "crop", "pest", "fertilizer", "irrigation"
        ]

        versions = db_session.query(PromptVersion).all()

        for version in versions:
            content_lower = version.content.lower()
            for term in forbidden_terms:
                assert term not in content_lower, (
                    f"Demo prompt contains domain-specific term: {term}"
                )

    def test_seed_demo_creates_greeting_prompt(self, db_session):
        """Test that demo greeting prompt is created."""
        seed_demo_prompts(db_session)

        greeting = db_session.query(PromptTemplate).filter(
            PromptTemplate.name == "demo_greeting_prompt"
        ).first()

        assert greeting is not None
        assert greeting.prompt_type == "greeting"

    def test_seed_demo_creates_fallback_prompt(self, db_session):
        """Test that demo fallback prompt is created."""
        seed_demo_prompts(db_session)

        fallback = db_session.query(PromptTemplate).filter(
            PromptTemplate.name == "demo_fallback_prompt"
        ).first()

        assert fallback is not None
        assert fallback.prompt_type == "fallback"
