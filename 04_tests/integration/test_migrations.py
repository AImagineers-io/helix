"""Integration tests for database migrations.

Tests verify pgvector migration behavior across PostgreSQL and SQLite.
"""
import pytest
import logging
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy import create_engine, text
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
