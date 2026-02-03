"""Database pre-flight checks for Helix.

This module provides capability detection for database features,
specifically pgvector support for vector operations.
"""
from dataclasses import dataclass, field
from typing import Optional, List

from sqlalchemy import text
from sqlalchemy.engine import Engine


@dataclass
class PreflightReport:
    """Report of database capabilities.

    Attributes:
        is_postgresql: Whether the database is PostgreSQL.
        has_pgvector: Whether pgvector extension is installed.
        pgvector_version: Version of pgvector if installed.
        can_create_vector_columns: Whether vector columns can be created.
        errors: List of errors encountered during checks.
    """

    is_postgresql: bool
    has_pgvector: bool
    pgvector_version: Optional[str]
    can_create_vector_columns: bool
    errors: List[str] = field(default_factory=list)


def check_database_capabilities(engine: Engine) -> PreflightReport:
    """Check database capabilities for vector support.

    Performs pre-flight checks to determine if the database supports
    vector operations (pgvector for PostgreSQL).

    Args:
        engine: SQLAlchemy engine instance to check.

    Returns:
        PreflightReport with capability flags and any errors.
    """
    is_postgresql = engine.dialect.name == "postgresql"
    has_pgvector = False
    pgvector_version = None
    can_create_vector_columns = False
    errors: List[str] = []

    if not is_postgresql:
        # SQLite or other database - no vector support
        return PreflightReport(
            is_postgresql=False,
            has_pgvector=False,
            pgvector_version=None,
            can_create_vector_columns=False,
            errors=["Database is not PostgreSQL - vector operations not supported"]
        )

    try:
        with engine.connect() as conn:
            # Check if pgvector extension exists
            result = conn.execute(
                text("SELECT extname FROM pg_extension WHERE extname = 'vector'")
            )
            row = result.fetchone()

            if row is not None:
                has_pgvector = True

                # Get pgvector version
                version_result = conn.execute(
                    text("SELECT extversion FROM pg_extension WHERE extname = 'vector'")
                )
                version_row = version_result.fetchone()
                if version_row:
                    pgvector_version = version_row[0]
                    can_create_vector_columns = True
            else:
                errors.append("pgvector extension not installed")

    except Exception as e:
        errors.append(f"Database check failed: {str(e)}")

    return PreflightReport(
        is_postgresql=is_postgresql,
        has_pgvector=has_pgvector,
        pgvector_version=pgvector_version,
        can_create_vector_columns=can_create_vector_columns,
        errors=errors
    )
