"""Unit tests for Embedding model.

Tests verify:
- Embedding model creation with vector storage
- Foreign key relationship to QAPair
- Model version tracking
- Conditional vector type (PostgreSQL vs SQLite)
- Cascade delete behavior
"""
import uuid
from datetime import datetime, timezone
from unittest.mock import Mock, patch

import pytest
from sqlalchemy import create_engine, select, JSON
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool


class TestEmbedding:
    """Tests for Embedding model."""

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

    @pytest.fixture
    def qa_pair(self, session):
        """Create a test QAPair for embedding tests."""
        from models.qa_pair import QAPair

        qa = QAPair(
            question="Test question?",
            answer="Test answer."
        )
        session.add(qa)
        session.commit()
        return qa

    def test_embedding_create(self, session, qa_pair):
        """Test that Embedding model instantiates with vector."""
        from models.embedding import Embedding

        # Create embedding with a sample vector (stored as JSON on SQLite)
        vector = [0.1] * 1536  # 1536-dimension vector
        embedding = Embedding(
            qa_pair_id=qa_pair.id,
            vector=vector,
            model_version="text-embedding-3-small"
        )
        session.add(embedding)
        session.commit()

        assert embedding.id is not None
        assert embedding.qa_pair_id == qa_pair.id
        assert embedding.model_version == "text-embedding-3-small"

    def test_embedding_links_qa_pair(self, session, qa_pair):
        """Test that foreign key to QAPair works."""
        from models.embedding import Embedding

        vector = [0.1] * 1536
        embedding = Embedding(
            qa_pair_id=qa_pair.id,
            vector=vector,
            model_version="test-model"
        )
        session.add(embedding)
        session.commit()

        # Verify relationship works
        session.refresh(embedding)
        assert embedding.qa_pair is not None
        assert embedding.qa_pair.id == qa_pair.id
        assert embedding.qa_pair.question == "Test question?"

    def test_embedding_tracks_model_version(self, session, qa_pair):
        """Test that model_version field exists and stores correctly."""
        from models.embedding import Embedding

        vector = [0.1] * 1536
        embedding = Embedding(
            qa_pair_id=qa_pair.id,
            vector=vector,
            model_version="text-embedding-3-large"
        )
        session.add(embedding)
        session.commit()

        session.refresh(embedding)
        assert embedding.model_version == "text-embedding-3-large"

    def test_embedding_vector_dimensions(self, session, qa_pair):
        """Test that vector stores 1536 dimensions."""
        from models.embedding import Embedding

        # Create a 1536-dimension vector
        vector = [0.001 * i for i in range(1536)]
        embedding = Embedding(
            qa_pair_id=qa_pair.id,
            vector=vector,
            model_version="test-model"
        )
        session.add(embedding)
        session.commit()

        session.refresh(embedding)

        # Vector should have 1536 elements
        assert len(embedding.vector) == 1536
        # Verify some values
        assert abs(embedding.vector[0] - 0.0) < 0.001
        assert abs(embedding.vector[100] - 0.1) < 0.001

    def test_embedding_cascade_delete(self, session, qa_pair):
        """Test that embedding is deleted when QAPair is deleted."""
        from models.embedding import Embedding
        from models.qa_pair import QAPair

        vector = [0.1] * 1536
        embedding = Embedding(
            qa_pair_id=qa_pair.id,
            vector=vector,
            model_version="test-model"
        )
        session.add(embedding)
        session.commit()

        embedding_id = embedding.id

        # Delete the QAPair
        session.delete(qa_pair)
        session.commit()

        # Embedding should be deleted too
        stmt = select(Embedding).where(Embedding.id == embedding_id)
        result = session.execute(stmt).scalar_one_or_none()
        assert result is None

    def test_embedding_one_to_one(self, session, qa_pair):
        """Test that embedding relationship is one-to-one."""
        from models.embedding import Embedding
        from sqlalchemy.exc import IntegrityError

        # Create first embedding
        vector1 = [0.1] * 1536
        embedding1 = Embedding(
            qa_pair_id=qa_pair.id,
            vector=vector1,
            model_version="model-v1"
        )
        session.add(embedding1)
        session.commit()

        # Try to create second embedding for same QAPair
        vector2 = [0.2] * 1536
        embedding2 = Embedding(
            qa_pair_id=qa_pair.id,
            vector=vector2,
            model_version="model-v2"
        )
        session.add(embedding2)

        with pytest.raises(IntegrityError):
            session.commit()

    def test_embedding_inherits_base_model(self, session, qa_pair):
        """Test that Embedding has BaseModel fields."""
        from models.embedding import Embedding

        vector = [0.1] * 1536
        embedding = Embedding(
            qa_pair_id=qa_pair.id,
            vector=vector,
            model_version="test-model"
        )
        session.add(embedding)
        session.commit()

        # Should have id, created_at, updated_at from BaseModel
        assert embedding.id is not None
        assert isinstance(embedding.id, uuid.UUID)
        assert embedding.created_at is not None
        assert embedding.updated_at is not None


class TestEmbeddingVectorType:
    """Tests for conditional vector type behavior."""

    def test_embedding_model_uses_json_on_sqlite(self):
        """Test that JSON type is used for vector on SQLite."""
        from database.vector import get_vector_column_type

        # Create SQLite engine
        engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool
        )

        vector_type = get_vector_column_type(engine, dimensions=1536)

        # Should be JSON for SQLite
        assert vector_type is JSON

    def test_embedding_model_uses_vector_on_postgresql(self):
        """Test that Vector type is used for PostgreSQL with pgvector."""
        from database.vector import get_vector_column_type
        from pgvector.sqlalchemy import Vector

        # Mock engine with PostgreSQL dialect and pgvector
        mock_engine = Mock()
        mock_engine.dialect.name = "postgresql"
        mock_conn = Mock()
        mock_result = Mock()
        mock_result.fetchone.return_value = ("vector",)
        mock_conn.execute.return_value = mock_result
        mock_conn.__enter__ = Mock(return_value=mock_conn)
        mock_conn.__exit__ = Mock(return_value=None)
        mock_engine.connect.return_value = mock_conn

        vector_type = get_vector_column_type(mock_engine, dimensions=1536)

        # Should be pgvector Vector type
        assert isinstance(vector_type, type(Vector(1536)))


class TestQAPairEmbeddingRelationship:
    """Tests for QAPair-Embedding relationship."""

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

        BaseModel.metadata.create_all(bind=engine)

        Session = sessionmaker(bind=engine)
        session = Session()
        yield session
        session.rollback()
        session.close()

    def test_qa_pair_can_access_embedding(self, session):
        """Test that QAPair can access its embedding."""
        from models.qa_pair import QAPair
        from models.embedding import Embedding

        # Create QAPair with embedding
        qa_pair = QAPair(
            question="Test?",
            answer="Test."
        )
        session.add(qa_pair)
        session.commit()

        vector = [0.1] * 1536
        embedding = Embedding(
            qa_pair_id=qa_pair.id,
            vector=vector,
            model_version="test-model"
        )
        session.add(embedding)
        session.commit()

        session.refresh(qa_pair)
        assert qa_pair.embedding is not None
        assert qa_pair.embedding.model_version == "test-model"
