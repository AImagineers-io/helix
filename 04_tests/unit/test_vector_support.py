"""Unit tests for vector support utilities.

Tests verify vector type detection and SQLite fallback behavior.
"""
import pytest
from unittest.mock import Mock, patch
from sqlalchemy import create_engine, JSON
from sqlalchemy.pool import StaticPool


class TestVectorDetection:
    """Tests for vector support detection."""

    def test_detects_postgresql_with_pgvector(self):
        """Test that PostgreSQL with pgvector is correctly detected."""
        from database.vector import has_vector_support

        # Mock engine with PostgreSQL dialect and pgvector available
        mock_engine = Mock()
        mock_engine.dialect.name = "postgresql"
        mock_conn = Mock()
        mock_result = Mock()
        mock_result.fetchone.return_value = ("vector",)
        mock_conn.execute.return_value = mock_result
        mock_conn.__enter__ = Mock(return_value=mock_conn)
        mock_conn.__exit__ = Mock(return_value=None)
        mock_engine.connect.return_value = mock_conn

        result = has_vector_support(mock_engine)

        assert result is True

    def test_detects_sqlite_no_vector(self):
        """Test that SQLite is detected as having no vector support."""
        from database.vector import has_vector_support

        # Use real SQLite engine
        engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool
        )

        result = has_vector_support(engine)

        assert result is False

    def test_detects_postgresql_without_pgvector(self):
        """Test detection when PostgreSQL doesn't have pgvector installed."""
        from database.vector import has_vector_support

        mock_engine = Mock()
        mock_engine.dialect.name = "postgresql"
        mock_conn = Mock()
        mock_result = Mock()
        mock_result.fetchone.return_value = None  # No extension found
        mock_conn.execute.return_value = mock_result
        mock_conn.__enter__ = Mock(return_value=mock_conn)
        mock_conn.__exit__ = Mock(return_value=None)
        mock_engine.connect.return_value = mock_conn

        result = has_vector_support(mock_engine)

        assert result is False


class TestVectorColumnType:
    """Tests for get_vector_column_type function."""

    def test_get_vector_column_type_postgresql(self):
        """Test that Vector type is returned for PostgreSQL with pgvector."""
        from database.vector import get_vector_column_type
        from pgvector.sqlalchemy import Vector

        # Mock engine with pgvector support
        mock_engine = Mock()
        mock_engine.dialect.name = "postgresql"
        mock_conn = Mock()
        mock_result = Mock()
        mock_result.fetchone.return_value = ("vector",)
        mock_conn.execute.return_value = mock_result
        mock_conn.__enter__ = Mock(return_value=mock_conn)
        mock_conn.__exit__ = Mock(return_value=None)
        mock_engine.connect.return_value = mock_conn

        result = get_vector_column_type(mock_engine, dimensions=1536)

        # Should be a pgvector Vector type
        assert isinstance(result, type(Vector(1536)))

    def test_get_vector_column_type_sqlite(self):
        """Test that JSON type is returned for SQLite."""
        from database.vector import get_vector_column_type

        # Real SQLite engine
        engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool
        )

        result = get_vector_column_type(engine, dimensions=1536)

        # Should be JSON for fallback
        assert result is JSON


class TestModelCompatibility:
    """Tests for model compatibility with vector fallback."""

    def test_qa_pair_model_loads_on_sqlite(self):
        """Test that QA pair model works on SQLite without pgvector errors."""
        from database.vector import get_vector_column_type

        # SQLite engine
        engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool
        )

        # Should not raise any errors
        vector_type = get_vector_column_type(engine, dimensions=1536)

        # Type should be usable (JSON for SQLite)
        assert vector_type is not None
        assert vector_type is JSON

    def test_embedding_model_uses_json_on_sqlite(self):
        """Test that embedding storage falls back to JSON on SQLite."""
        from database.vector import get_vector_column_type

        # SQLite engine
        engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool
        )

        vector_type = get_vector_column_type(engine, dimensions=1536)

        # Should use JSON as fallback
        assert vector_type is JSON


class TestPytestMarker:
    """Tests for the requires_pgvector marker."""

    def test_requires_pgvector_marker_exists(self):
        """Test that requires_pgvector marker is available."""
        from database.vector import requires_pgvector

        assert requires_pgvector is not None
        # Should be a pytest marker or skip decorator
        assert callable(requires_pgvector) or hasattr(requires_pgvector, 'mark')

    def test_requires_pgvector_skips_on_sqlite(self):
        """Test that requires_pgvector creates a skip condition."""
        from database.vector import create_requires_pgvector_marker

        # Create marker for SQLite (no vector support)
        engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool
        )

        marker = create_requires_pgvector_marker(engine)

        # Should be a skipif marker
        assert hasattr(marker, 'mark') or 'skip' in str(marker)
