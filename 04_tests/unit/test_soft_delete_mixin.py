"""Unit tests for SoftDeleteMixin.

Tests verify the soft delete mixin provides:
- deleted_at timestamp field
- is_deleted property
- active() query filter
"""
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine, String, select
from sqlalchemy.orm import sessionmaker, Mapped, mapped_column
from sqlalchemy.pool import StaticPool


def get_soft_delete_test_model():
    """Get or create the SoftDeleteTestModel class."""
    from models.base import BaseModel
    from models.mixins import SoftDeleteMixin

    # Check if model is already defined in the registry
    for mapper in BaseModel.registry.mappers:
        if mapper.class_.__name__ == "SoftDeleteTestModel":
            return mapper.class_

    class SoftDeleteTestModel(BaseModel, SoftDeleteMixin):
        """Test model for verifying SoftDeleteMixin functionality."""
        __tablename__ = "soft_delete_test"

        name: Mapped[str] = mapped_column(String(100), nullable=True)

    return SoftDeleteTestModel


class TestSoftDeleteMixin:
    """Tests for SoftDeleteMixin."""

    @pytest.fixture
    def engine(self):
        """Create in-memory SQLite engine for testing."""
        return create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool
        )

    @pytest.fixture
    def test_model_class(self):
        """Get the test model class."""
        return get_soft_delete_test_model()

    @pytest.fixture
    def session(self, engine, test_model_class):
        """Create database session with tables."""
        from models.base import BaseModel

        # Create all tables
        BaseModel.metadata.create_all(bind=engine)

        Session = sessionmaker(bind=engine)
        session = Session()
        yield session
        session.rollback()
        session.close()

    def test_soft_delete_has_deleted_at_field(self, test_model_class):
        """Test that SoftDeleteMixin provides deleted_at field."""
        instance = test_model_class()

        # deleted_at field should exist
        assert hasattr(instance, 'deleted_at')

    def test_soft_delete_deleted_at_nullable(self, session, test_model_class):
        """Test that deleted_at is nullable (None by default)."""
        instance = test_model_class(name="test")
        session.add(instance)
        session.commit()

        # deleted_at should be None for non-deleted record
        assert instance.deleted_at is None

    def test_soft_delete_sets_deleted_at(self, session, test_model_class):
        """Test that soft delete populates deleted_at timestamp."""
        instance = test_model_class(name="to_delete")
        session.add(instance)
        session.commit()

        # Set deleted_at to mark as deleted
        instance.deleted_at = datetime.now(timezone.utc)
        session.commit()

        # deleted_at should be populated
        assert instance.deleted_at is not None
        assert isinstance(instance.deleted_at, datetime)

    def test_is_deleted_property_false_when_not_deleted(self, session, test_model_class):
        """Test is_deleted returns False when deleted_at is None."""
        instance = test_model_class(name="active")
        session.add(instance)
        session.commit()

        # is_deleted should be False
        assert instance.is_deleted is False

    def test_is_deleted_property_true_when_deleted(self, session, test_model_class):
        """Test is_deleted returns True when deleted_at is set."""
        instance = test_model_class(name="deleted")
        instance.deleted_at = datetime.now(timezone.utc)
        session.add(instance)
        session.commit()

        # is_deleted should be True
        assert instance.is_deleted is True

    def test_active_query_excludes_deleted(self, session, test_model_class):
        """Test that active() filter excludes deleted records."""
        # Create active record
        active_instance = test_model_class(name="active")
        session.add(active_instance)

        # Create deleted record
        deleted_instance = test_model_class(name="deleted")
        deleted_instance.deleted_at = datetime.now(timezone.utc)
        session.add(deleted_instance)

        session.commit()

        # Query with active filter
        stmt = select(test_model_class).where(test_model_class.active())
        results = session.execute(stmt).scalars().all()

        # Should only include active record
        assert len(results) == 1
        assert results[0].name == "active"

    def test_active_query_includes_all_non_deleted(self, session, test_model_class):
        """Test that active() includes all records where deleted_at is None."""
        # Create multiple active records
        for i in range(3):
            instance = test_model_class(name=f"active_{i}")
            session.add(instance)

        session.commit()

        # Query with active filter
        stmt = select(test_model_class).where(test_model_class.active())
        results = session.execute(stmt).scalars().all()

        # Should include all 3 active records
        assert len(results) == 3

    def test_soft_delete_preserves_record(self, session, test_model_class):
        """Test that soft delete keeps the record in database."""
        instance = test_model_class(name="preserved")
        session.add(instance)
        session.commit()

        instance_id = instance.id

        # Soft delete
        instance.deleted_at = datetime.now(timezone.utc)
        session.commit()

        # Record should still exist in database
        stmt = select(test_model_class).where(test_model_class.id == instance_id)
        result = session.execute(stmt).scalar_one_or_none()

        assert result is not None
        assert result.name == "preserved"
        assert result.is_deleted is True
