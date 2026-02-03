"""Vector support utilities for Helix.

This module provides vector type detection and SQLite fallback for RAG operations.
Supports pgvector for PostgreSQL and JSON fallback for SQLite testing.
"""
import pytest
from typing import Any

from sqlalchemy import text, JSON
from sqlalchemy.engine import Engine


def has_vector_support(engine: Engine) -> bool:
    """Check if database supports vector operations.

    Detects PostgreSQL with pgvector extension installed.
    Returns False for SQLite or PostgreSQL without pgvector.

    Args:
        engine: SQLAlchemy engine instance to check.

    Returns:
        True if database supports vector operations, False otherwise.
    """
    if engine.dialect.name != "postgresql":
        return False

    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT extname FROM pg_extension WHERE extname = 'vector'")
            )
            row = result.fetchone()
            return row is not None
    except Exception:
        return False


def get_vector_column_type(engine: Engine, dimensions: int = 1536) -> Any:
    """Get appropriate column type for vector storage.

    Returns pgvector Vector type for PostgreSQL with pgvector extension,
    or JSON type as fallback for SQLite and PostgreSQL without pgvector.

    Args:
        engine: SQLAlchemy engine instance.
        dimensions: Number of dimensions for the vector (default 1536 for OpenAI).

    Returns:
        SQLAlchemy column type (Vector or JSON).
    """
    if has_vector_support(engine):
        from pgvector.sqlalchemy import Vector
        return Vector(dimensions)

    # Fallback to JSON for SQLite or PostgreSQL without pgvector
    return JSON


def create_requires_pgvector_marker(engine: Engine):
    """Create a pytest marker for tests requiring pgvector.

    Creates a skipif marker that skips tests when pgvector is not available.

    Args:
        engine: SQLAlchemy engine instance to check.

    Returns:
        pytest.mark.skipif decorator.
    """
    return pytest.mark.skipif(
        not has_vector_support(engine),
        reason="Requires PostgreSQL with pgvector extension"
    )


# Default marker using the module-level check
# This can be overridden in conftest.py with a specific engine
def _get_default_requires_pgvector():
    """Get default requires_pgvector marker.

    Returns a marker that always skips (no database configured).
    Override in conftest.py for actual database testing.
    """
    return pytest.mark.skipif(
        True,
        reason="Requires PostgreSQL with pgvector extension (no engine configured)"
    )


requires_pgvector = _get_default_requires_pgvector()
