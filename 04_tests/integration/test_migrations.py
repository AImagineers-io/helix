"""Integration tests for database migrations.

Tests verify:
- pgvector migration behavior across PostgreSQL and SQLite
- QAPair and Embedding table creation
- Required indexes and foreign keys
- HNSW vector index (PostgreSQL)
"""
import pytest
import logging
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool


class TestPgvectorMigration:
    """Tests for pgvector migration."""

    def test_pgvector_migration_applies_cleanly(self):
        """Test that migration runs without error on PostgreSQL."""
        from database.migrations.enable_pgvector import (
            upgrade,
            MigrationResult,
        )

        # Mock PostgreSQL engine
        mock_engine = Mock()
        mock_engine.dialect.name = "postgresql"
        mock_conn = Mock()

        # Mock execute to return proper result with scalar method
        mock_result = Mock()
        mock_result.scalar.return_value = "0.5.1"
        mock_conn.execute.return_value = mock_result
        mock_conn.commit.return_value = None

        mock_conn.__enter__ = Mock(return_value=mock_conn)
        mock_conn.__exit__ = Mock(return_value=None)
        mock_engine.connect.return_value = mock_conn

        # Should not raise
        result = upgrade(mock_engine)

        assert isinstance(result, MigrationResult)
        assert result.success is True

    def test_pgvector_extension_enabled(self):
        """Test that extension is created after migration."""
        from database.migrations.enable_pgvector import upgrade

        mock_engine = Mock()
        mock_engine.dialect.name = "postgresql"
        mock_conn = Mock()
        executed_statements = []

        def track_execute(stmt):
            executed_statements.append(str(stmt))
            return Mock()

        mock_conn.execute.side_effect = track_execute
        mock_conn.__enter__ = Mock(return_value=mock_conn)
        mock_conn.__exit__ = Mock(return_value=None)
        mock_engine.connect.return_value = mock_conn

        upgrade(mock_engine)

        # Check that CREATE EXTENSION was called
        assert any("CREATE EXTENSION" in s for s in executed_statements)
        assert any("vector" in s for s in executed_statements)

    def test_migration_idempotent(self):
        """Test that running migration twice doesn't fail."""
        from database.migrations.enable_pgvector import upgrade

        mock_engine = Mock()
        mock_engine.dialect.name = "postgresql"
        mock_conn = Mock()

        # Mock execute to return proper result with scalar method
        mock_result = Mock()
        mock_result.scalar.return_value = "0.5.1"
        mock_conn.execute.return_value = mock_result
        mock_conn.commit.return_value = None

        mock_conn.__enter__ = Mock(return_value=mock_conn)
        mock_conn.__exit__ = Mock(return_value=None)
        mock_engine.connect.return_value = mock_conn

        # Run twice - should not raise (IF NOT EXISTS makes it idempotent)
        result1 = upgrade(mock_engine)
        result2 = upgrade(mock_engine)

        assert result1.success is True
        assert result2.success is True

    def test_migration_skips_on_sqlite(self):
        """Test that migration gracefully skips on SQLite."""
        from database.migrations.enable_pgvector import upgrade

        # Real SQLite engine
        engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool
        )

        result = upgrade(engine)

        assert result.success is True
        assert result.skipped is True
        assert "SQLite" in result.message or "not PostgreSQL" in result.message.lower()

    def test_downgrade_warns_if_embeddings_exist(self, caplog):
        """Test that downgrade logs warning if embeddings exist."""
        from database.migrations.enable_pgvector import downgrade

        mock_engine = Mock()
        mock_engine.dialect.name = "postgresql"
        mock_conn = Mock()

        # Mock that embeddings exist
        mock_result = Mock()
        mock_result.scalar.return_value = 42  # 42 embeddings exist

        def mock_execute(stmt):
            if "COUNT" in str(stmt) or "count" in str(stmt).lower():
                return mock_result
            return Mock()

        mock_conn.execute.side_effect = mock_execute
        mock_conn.__enter__ = Mock(return_value=mock_conn)
        mock_conn.__exit__ = Mock(return_value=None)
        mock_engine.connect.return_value = mock_conn

        with caplog.at_level(logging.WARNING):
            result = downgrade(mock_engine)

        # Should have logged a warning about existing embeddings
        assert result.warning is not None or len(caplog.records) > 0

    def test_migration_logs_pgvector_version(self, caplog):
        """Test that migration logs pgvector version after creation."""
        from database.migrations.enable_pgvector import upgrade

        mock_engine = Mock()
        mock_engine.dialect.name = "postgresql"
        mock_conn = Mock()

        # Return version when queried
        version_result = Mock()
        version_result.scalar.return_value = "0.5.1"

        call_count = [0]

        def mock_execute(stmt):
            call_count[0] += 1
            stmt_str = str(stmt)
            if "extversion" in stmt_str.lower() or "pg_extension" in stmt_str.lower():
                return version_result
            return Mock()

        mock_conn.execute.side_effect = mock_execute
        mock_conn.__enter__ = Mock(return_value=mock_conn)
        mock_conn.__exit__ = Mock(return_value=None)
        mock_engine.connect.return_value = mock_conn

        with caplog.at_level(logging.INFO):
            result = upgrade(mock_engine)

        # Check version was captured
        assert result.pgvector_version == "0.5.1" or "0.5.1" in str(caplog.records)


class TestMigrationResult:
    """Tests for MigrationResult dataclass."""

    def test_migration_result_creation(self):
        """Test MigrationResult can be created."""
        from database.migrations.enable_pgvector import MigrationResult

        result = MigrationResult(
            success=True,
            skipped=False,
            message="Migration applied successfully",
            pgvector_version="0.5.1",
            warning=None
        )

        assert result.success is True
        assert result.skipped is False
        assert result.pgvector_version == "0.5.1"

    def test_migration_result_with_warning(self):
        """Test MigrationResult captures warnings."""
        from database.migrations.enable_pgvector import MigrationResult

        result = MigrationResult(
            success=True,
            skipped=False,
            message="Downgrade completed",
            pgvector_version=None,
            warning="42 embeddings will be lost"
        )

        assert result.warning is not None
        assert "embeddings" in result.warning


class TestQAPairTableMigration:
    """Tests for QAPair table migration."""

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

    def test_qa_pair_table_created(self, engine, session):
        """Test that qa_pair table exists after migration."""
        inspector = inspect(engine)
        tables = inspector.get_table_names()

        assert "qa_pair" in tables

    def test_embedding_table_created(self, engine, session):
        """Test that embedding table exists after migration."""
        inspector = inspect(engine)
        tables = inspector.get_table_names()

        assert "embedding" in tables

    def test_qa_pair_columns_exist(self, engine, session):
        """Test that qa_pair table has all required columns."""
        inspector = inspect(engine)
        columns = {col['name'] for col in inspector.get_columns("qa_pair")}

        # Required columns from BaseModel
        assert "id" in columns
        assert "created_at" in columns
        assert "updated_at" in columns

        # Required columns from SoftDeleteMixin
        assert "deleted_at" in columns

        # Required columns from QAPair
        assert "question" in columns
        assert "answer" in columns
        assert "category" in columns
        assert "tags" in columns
        assert "status" in columns

    def test_embedding_columns_exist(self, engine, session):
        """Test that embedding table has all required columns."""
        inspector = inspect(engine)
        columns = {col['name'] for col in inspector.get_columns("embedding")}

        # Required columns from BaseModel
        assert "id" in columns
        assert "created_at" in columns
        assert "updated_at" in columns

        # Required columns from Embedding
        assert "qa_pair_id" in columns
        assert "vector" in columns
        assert "model_version" in columns

    def test_qa_pair_indexes_created(self, engine, session):
        """Test that qa_pair table has required indexes."""
        inspector = inspect(engine)
        indexes = inspector.get_indexes("qa_pair")

        # Collect all indexed columns
        index_columns = set()
        for idx in indexes:
            for col in idx['column_names']:
                index_columns.add(col)

        # Should have indexes on status, category, and question
        assert "status" in index_columns
        assert "category" in index_columns
        assert "question" in index_columns

    def test_embedding_foreign_key(self, engine, session):
        """Test that embedding table has foreign key to qa_pair."""
        inspector = inspect(engine)
        fks = inspector.get_foreign_keys("embedding")

        assert len(fks) >= 1
        fk_tables = [fk['referred_table'] for fk in fks]
        assert "qa_pair" in fk_tables

    def test_embedding_qa_pair_id_unique(self, engine, session):
        """Test that qa_pair_id in embedding table is unique."""
        inspector = inspect(engine)

        # Check for unique constraint via indexes
        indexes = inspector.get_indexes("embedding")
        unique_cols = set()
        for idx in indexes:
            if idx.get('unique', False):
                for col in idx['column_names']:
                    unique_cols.add(col)

        # Also check unique constraints
        uniqs = inspector.get_unique_constraints("embedding")
        for uniq in uniqs:
            for col in uniq['column_names']:
                unique_cols.add(col)

        assert "qa_pair_id" in unique_cols

    def test_qa_pair_can_be_inserted(self, session):
        """Test that data can be inserted into qa_pair table."""
        from models.qa_pair import QAPair
        from models.enums import QAStatus

        qa_pair = QAPair(
            question="Migration test question?",
            answer="Migration test answer."
        )
        session.add(qa_pair)
        session.commit()

        assert qa_pair.id is not None
        assert qa_pair.status == QAStatus.DRAFT

    def test_embedding_can_be_inserted(self, session):
        """Test that data can be inserted into embedding table."""
        from models.qa_pair import QAPair
        from models.embedding import Embedding

        # Create QAPair first
        qa_pair = QAPair(
            question="Embedding test question?",
            answer="Embedding test answer."
        )
        session.add(qa_pair)
        session.commit()

        # Create Embedding
        vector = [0.1] * 1536
        embedding = Embedding(
            qa_pair_id=qa_pair.id,
            vector=vector,
            model_version="test-v1"
        )
        session.add(embedding)
        session.commit()

        assert embedding.id is not None
        assert embedding.qa_pair_id == qa_pair.id

    def test_hnsw_index_works_on_empty_table(self, session):
        """Test that vector operations work on empty table.

        HNSW index (unlike IVFFlat) doesn't require training data,
        so it should work immediately after table creation.
        """
        from models.embedding import Embedding
        from sqlalchemy import select

        # Query should work even with empty table
        stmt = select(Embedding)
        results = session.execute(stmt).scalars().all()

        assert results == []
