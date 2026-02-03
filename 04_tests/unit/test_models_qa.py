"""Unit tests for QAStatus enum and QAPair model.

Tests verify:
- QAStatus enum values (DRAFT, ACTIVE, ARCHIVED)
- QAPair model fields and behavior
"""
import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool


class TestQAStatus:
    """Tests for QAStatus enum."""

    def test_qa_status_has_draft(self):
        """Test that QAStatus has DRAFT value."""
        from models.enums import QAStatus

        assert hasattr(QAStatus, 'DRAFT')
        assert QAStatus.DRAFT is not None

    def test_qa_status_has_active(self):
        """Test that QAStatus has ACTIVE value."""
        from models.enums import QAStatus

        assert hasattr(QAStatus, 'ACTIVE')
        assert QAStatus.ACTIVE is not None

    def test_qa_status_has_archived(self):
        """Test that QAStatus has ARCHIVED value."""
        from models.enums import QAStatus

        assert hasattr(QAStatus, 'ARCHIVED')
        assert QAStatus.ARCHIVED is not None

    def test_qa_status_values_are_strings(self):
        """Test that QAStatus values are string-based."""
        from models.enums import QAStatus

        assert QAStatus.DRAFT.value == "draft"
        assert QAStatus.ACTIVE.value == "active"
        assert QAStatus.ARCHIVED.value == "archived"


class TestQAPair:
    """Tests for QAPair model."""

    @pytest.fixture
    def engine(self):
        """Create in-memory SQLite engine for testing."""
        return create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool
        )

    @pytest.fixture
    def session(self, engine):
        """Create database session with tables."""
        from models.base import BaseModel

        # Create all tables
        BaseModel.metadata.create_all(bind=engine)

        Session = sessionmaker(bind=engine)
        session = Session()
        yield session
        session.rollback()
        session.close()

    def test_qa_pair_create(self):
        """Test that QAPair model instantiates with required fields."""
        from models.qa_pair import QAPair

        qa_pair = QAPair(
            question="What is the return policy?",
            answer="You can return items within 30 days."
        )

        assert qa_pair.question == "What is the return policy?"
        assert qa_pair.answer == "You can return items within 30 days."

    def test_qa_pair_defaults(self, session):
        """Test that QAPair has correct default values."""
        from models.qa_pair import QAPair
        from models.enums import QAStatus

        qa_pair = QAPair(
            question="Test question?",
            answer="Test answer."
        )
        session.add(qa_pair)
        session.commit()

        # Status should default to DRAFT
        assert qa_pair.status == QAStatus.DRAFT

        # Timestamps should be set
        assert qa_pair.created_at is not None
        assert qa_pair.updated_at is not None

    def test_qa_pair_soft_delete(self, session):
        """Test that QAPair has soft delete functionality."""
        from models.qa_pair import QAPair

        qa_pair = QAPair(
            question="To be deleted?",
            answer="Will be soft deleted."
        )
        session.add(qa_pair)
        session.commit()

        # deleted_at should exist and be None initially
        assert hasattr(qa_pair, 'deleted_at')
        assert qa_pair.deleted_at is None

        # Can set deleted_at
        qa_pair.deleted_at = datetime.now(timezone.utc)
        session.commit()
        assert qa_pair.deleted_at is not None

    def test_qa_pair_tags_json(self, session):
        """Test that tags are stored as JSON array."""
        from models.qa_pair import QAPair

        qa_pair = QAPair(
            question="Tagged question?",
            answer="Tagged answer.",
            tags=["faq", "returns", "policy"]
        )
        session.add(qa_pair)
        session.commit()

        # Refresh to get from database
        session.refresh(qa_pair)

        assert qa_pair.tags == ["faq", "returns", "policy"]
        assert isinstance(qa_pair.tags, list)

    def test_qa_pair_tags_default_empty(self, session):
        """Test that tags default to empty list."""
        from models.qa_pair import QAPair

        qa_pair = QAPair(
            question="No tags?",
            answer="No tags."
        )
        session.add(qa_pair)
        session.commit()
        session.refresh(qa_pair)

        assert qa_pair.tags == []

    def test_qa_pair_requires_question(self, session):
        """Test that question field is required (not nullable)."""
        from models.qa_pair import QAPair
        from sqlalchemy.exc import IntegrityError

        qa_pair = QAPair(answer="Answer without question")

        session.add(qa_pair)

        with pytest.raises(IntegrityError):
            session.commit()

    def test_qa_pair_requires_answer(self, session):
        """Test that answer field is required (not nullable)."""
        from models.qa_pair import QAPair
        from sqlalchemy.exc import IntegrityError

        qa_pair = QAPair(question="Question without answer?")

        session.add(qa_pair)

        with pytest.raises(IntegrityError):
            session.commit()

    def test_qa_pair_inherits_base(self):
        """Test that QAPair has id, created_at, updated_at from BaseModel."""
        from models.qa_pair import QAPair

        qa_pair = QAPair(
            question="Test?",
            answer="Test."
        )

        assert hasattr(qa_pair, 'id')
        assert hasattr(qa_pair, 'created_at')
        assert hasattr(qa_pair, 'updated_at')

    def test_qa_pair_has_soft_delete(self):
        """Test that QAPair has soft delete fields from SoftDeleteMixin."""
        from models.qa_pair import QAPair

        qa_pair = QAPair(
            question="Test?",
            answer="Test."
        )

        # Should have deleted_at, is_deleted, and active()
        assert hasattr(qa_pair, 'deleted_at')
        assert hasattr(qa_pair, 'is_deleted')
        assert hasattr(QAPair, 'active')
        assert callable(QAPair.active)

    def test_qa_pair_category_optional(self, session):
        """Test that category field is optional."""
        from models.qa_pair import QAPair

        # Without category
        qa_pair = QAPair(
            question="No category?",
            answer="No category."
        )
        session.add(qa_pair)
        session.commit()

        assert qa_pair.category is None

    def test_qa_pair_category_can_be_set(self, session):
        """Test that category can be set."""
        from models.qa_pair import QAPair

        qa_pair = QAPair(
            question="With category?",
            answer="Has category.",
            category="Returns"
        )
        session.add(qa_pair)
        session.commit()

        assert qa_pair.category == "Returns"

    def test_qa_pair_uuid_generated(self, session):
        """Test that QAPair gets UUID id on create."""
        from models.qa_pair import QAPair

        qa_pair = QAPair(
            question="UUID test?",
            answer="UUID test."
        )
        session.add(qa_pair)
        session.commit()

        assert qa_pair.id is not None
        assert isinstance(qa_pair.id, uuid.UUID)

    def test_qa_pair_active_filter(self, session):
        """Test that active() filter works on QAPair."""
        from models.qa_pair import QAPair

        # Create active record
        active = QAPair(question="Active?", answer="Active.")
        session.add(active)

        # Create deleted record
        deleted = QAPair(question="Deleted?", answer="Deleted.")
        deleted.deleted_at = datetime.now(timezone.utc)
        session.add(deleted)

        session.commit()

        # Query with active filter
        stmt = select(QAPair).where(QAPair.active())
        results = session.execute(stmt).scalars().all()

        assert len(results) == 1
        assert results[0].question == "Active?"
