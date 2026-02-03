"""Unit tests for package imports.

Tests verify that required packages can be imported successfully.
"""
import pytest


def test_pgvector_package_importable():
    """Test that pgvector package imports without error.

    Verifies the pgvector SQLAlchemy integration is available
    for vector column type support.
    """
    try:
        from pgvector.sqlalchemy import Vector
        assert Vector is not None
    except ImportError as e:
        pytest.fail(f"pgvector package not importable: {e}")


def test_pgvector_has_vector_type():
    """Test that pgvector Vector type is usable.

    Verifies we can create a Vector type with dimensions.
    """
    from pgvector.sqlalchemy import Vector

    # Should be able to create a Vector type with dimensions
    vector_type = Vector(1536)
    assert vector_type is not None
