"""Unit tests for database pre-flight checks.

Tests verify database capability detection for vector support.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool


class TestPreflightReport:
    """Tests for PreflightReport dataclass."""

    def test_preflight_report_creation(self):
        """Test that PreflightReport can be created with all fields."""
        from database.preflight import PreflightReport

        report = PreflightReport(
            is_postgresql=True,
            has_pgvector=True,
            pgvector_version="0.5.1",
            can_create_vector_columns=True,
            errors=[]
        )

        assert report.is_postgresql is True
        assert report.has_pgvector is True
        assert report.pgvector_version == "0.5.1"
        assert report.can_create_vector_columns is True
        assert report.errors == []

    def test_preflight_report_with_errors(self):
        """Test that PreflightReport captures errors."""
        from database.preflight import PreflightReport

        report = PreflightReport(
            is_postgresql=False,
            has_pgvector=False,
            pgvector_version=None,
            can_create_vector_columns=False,
            errors=["Not PostgreSQL", "pgvector not installed"]
        )

        assert len(report.errors) == 2
        assert "Not PostgreSQL" in report.errors


class TestDatabaseCapabilityCheck:
    """Tests for check_database_capabilities function."""

    def test_check_postgresql_connection(self):
        """Test that PostgreSQL connection is properly detected."""
        from database.preflight import check_database_capabilities

        # Create a mock engine that looks like PostgreSQL
        mock_engine = Mock()
        mock_engine.dialect.name = "postgresql"
        mock_conn = Mock()
        mock_result = Mock()
        mock_result.fetchone.return_value = ("0.5.1",)
        mock_conn.execute.return_value = mock_result
        mock_conn.__enter__ = Mock(return_value=mock_conn)
        mock_conn.__exit__ = Mock(return_value=None)
        mock_engine.connect.return_value = mock_conn

        report = check_database_capabilities(mock_engine)

        assert report.is_postgresql is True

    def test_check_pgvector_extension_exists(self):
        """Test detection of pgvector extension when installed."""
        from database.preflight import check_database_capabilities

        # Mock PostgreSQL with pgvector
        mock_engine = Mock()
        mock_engine.dialect.name = "postgresql"
        mock_conn = Mock()

        # First call returns extension exists, second returns version
        mock_result_exists = Mock()
        mock_result_exists.fetchone.return_value = ("vector",)

        mock_result_version = Mock()
        mock_result_version.fetchone.return_value = ("0.5.1",)

        mock_conn.execute.side_effect = [mock_result_exists, mock_result_version]
        mock_conn.__enter__ = Mock(return_value=mock_conn)
        mock_conn.__exit__ = Mock(return_value=None)
        mock_engine.connect.return_value = mock_conn

        report = check_database_capabilities(mock_engine)

        assert report.has_pgvector is True

    def test_check_pgvector_version(self):
        """Test that pgvector version is correctly retrieved."""
        from database.preflight import check_database_capabilities

        mock_engine = Mock()
        mock_engine.dialect.name = "postgresql"
        mock_conn = Mock()

        # Return extension exists and version
        mock_result_exists = Mock()
        mock_result_exists.fetchone.return_value = ("vector",)

        mock_result_version = Mock()
        mock_result_version.fetchone.return_value = ("0.6.0",)

        mock_conn.execute.side_effect = [mock_result_exists, mock_result_version]
        mock_conn.__enter__ = Mock(return_value=mock_conn)
        mock_conn.__exit__ = Mock(return_value=None)
        mock_engine.connect.return_value = mock_conn

        report = check_database_capabilities(mock_engine)

        assert report.pgvector_version == "0.6.0"

    def test_preflight_returns_report(self):
        """Test that check returns a proper PreflightReport structure."""
        from database.preflight import check_database_capabilities, PreflightReport

        mock_engine = Mock()
        mock_engine.dialect.name = "postgresql"
        mock_conn = Mock()
        mock_result = Mock()
        mock_result.fetchone.return_value = ("vector",)
        mock_result_version = Mock()
        mock_result_version.fetchone.return_value = ("0.5.1",)
        mock_conn.execute.side_effect = [mock_result, mock_result_version]
        mock_conn.__enter__ = Mock(return_value=mock_conn)
        mock_conn.__exit__ = Mock(return_value=None)
        mock_engine.connect.return_value = mock_conn

        report = check_database_capabilities(mock_engine)

        assert isinstance(report, PreflightReport)
        assert hasattr(report, 'is_postgresql')
        assert hasattr(report, 'has_pgvector')
        assert hasattr(report, 'pgvector_version')
        assert hasattr(report, 'can_create_vector_columns')
        assert hasattr(report, 'errors')

    def test_check_sqlite_detected(self):
        """Test that SQLite is correctly identified as non-PostgreSQL."""
        from database.preflight import check_database_capabilities

        # Use real SQLite engine
        engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool
        )

        report = check_database_capabilities(engine)

        assert report.is_postgresql is False
        assert report.has_pgvector is False
        assert report.can_create_vector_columns is False

    def test_check_pgvector_not_installed(self):
        """Test detection when pgvector extension is not installed."""
        from database.preflight import check_database_capabilities

        mock_engine = Mock()
        mock_engine.dialect.name = "postgresql"
        mock_conn = Mock()

        # Return no extension found
        mock_result = Mock()
        mock_result.fetchone.return_value = None
        mock_conn.execute.return_value = mock_result
        mock_conn.__enter__ = Mock(return_value=mock_conn)
        mock_conn.__exit__ = Mock(return_value=None)
        mock_engine.connect.return_value = mock_conn

        report = check_database_capabilities(mock_engine)

        assert report.has_pgvector is False
        assert report.pgvector_version is None

    def test_check_handles_connection_error(self):
        """Test that connection errors are handled gracefully."""
        from database.preflight import check_database_capabilities

        mock_engine = Mock()
        mock_engine.dialect.name = "postgresql"
        mock_engine.connect.side_effect = Exception("Connection refused")

        report = check_database_capabilities(mock_engine)

        assert report.is_postgresql is True  # Still detected from dialect
        assert report.has_pgvector is False
        assert len(report.errors) > 0
        assert "Connection refused" in str(report.errors)
