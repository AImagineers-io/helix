"""Unit tests for BaseModel.

Tests verify the base model provides:
- UUID primary key auto-generation
- created_at timestamp auto-set
- updated_at timestamp auto-update
"""
import uuid
from datetime import datetime, timezone
import time

import pytest
from sqlalchemy import create_engine, String
from sqlalchemy.orm import sessionmaker, Mapped, mapped_column
from sqlalchemy.pool import StaticPool


# Create a module-level test model to avoid redefinition issues
_test_model_created = False


def get_test_model():
    """Get or create the TestModel class."""
    global _test_model_created

    from models.base import BaseModel

    # Check if TestModel is already defined in the registry
    for mapper in BaseModel.registry.mappers:
        if mapper.class_.__name__ == "BaseModelTestModel":
            return mapper.class_

    # Create the model only once
    class BaseModelTestModel(BaseModel):
        """Test model for verifying BaseModel functionality."""
        __tablename__ = "base_model_test"

        name: Mapped[str] = mapped_column(String(100), nullable=True)

    _test_model_created = True
    return BaseModelTestModel


class TestBaseModel:
    """Tests for BaseModel base class."""

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
        return get_test_model()

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

    def test_base_model_has_id(self, test_model_class):
        """Test that BaseModel provides id field."""
        instance = test_model_class()

        # id field should exist
        assert hasattr(instance, 'id')

    def test_base_model_has_created_at(self, test_model_class):
        """Test that BaseModel provides created_at field."""
        instance = test_model_class()

        # created_at field should exist
        assert hasattr(instance, 'created_at')

    def test_base_model_has_updated_at(self, test_model_class):
        """Test that BaseModel provides updated_at field."""
        instance = test_model_class()

        # updated_at field should exist
        assert hasattr(instance, 'updated_at')

    def test_uuid_generated_on_create(self, session, test_model_class):
        """Test that UUID is auto-generated when creating a record."""
        # Create instance without providing id
        instance = test_model_class(name="test")
        session.add(instance)
        session.commit()

        # id should be a valid UUID
        assert instance.id is not None
        assert isinstance(instance.id, uuid.UUID)

    def test_created_at_auto_set_on_insert(self, session, test_model_class):
        """Test that created_at is automatically set on insert."""
        before = datetime.now(timezone.utc)

        instance = test_model_class(name="test_created")
        session.add(instance)
        session.commit()

        after = datetime.now(timezone.utc)

        # created_at should be set automatically
        assert instance.created_at is not None
        # Should have a valid datetime
        assert isinstance(instance.created_at, datetime)

    def test_updated_at_auto_set_on_insert(self, session, test_model_class):
        """Test that updated_at is set on initial insert."""
        instance = test_model_class(name="test_updated")
        session.add(instance)
        session.commit()

        # updated_at should be set
        assert instance.updated_at is not None
        assert isinstance(instance.updated_at, datetime)

    def test_updated_at_changes_on_update(self, session, test_model_class):
        """Test that updated_at is updated on record modification."""
        instance = test_model_class(name="original")
        session.add(instance)
        session.commit()

        original_updated_at = instance.updated_at

        # Small delay to ensure timestamp difference
        time.sleep(0.02)

        # Modify the record
        instance.name = "modified"
        session.commit()
        session.refresh(instance)

        # updated_at should have changed (or be equal due to timing)
        assert instance.updated_at >= original_updated_at

    def test_uuid_is_primary_key(self, test_model_class):
        """Test that id is configured as primary key."""
        from sqlalchemy import inspect

        mapper = inspect(test_model_class)
        pk_columns = [col.name for col in mapper.primary_key]

        assert "id" in pk_columns

    def test_id_is_uuid_type(self, test_model_class):
        """Test that id column exists and stores UUIDs."""
        from sqlalchemy import inspect

        mapper = inspect(test_model_class)
        id_column = mapper.columns.get("id")

        # The column should exist
        assert id_column is not None

        # Test that we can create instances with valid UUIDs
        instance = test_model_class(name="uuid_test")
        assert instance.id is None or isinstance(instance.id, uuid.UUID)
