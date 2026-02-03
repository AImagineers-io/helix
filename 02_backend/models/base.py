"""Base model for Helix knowledge base models.

Provides common fields and functionality for all models:
- UUID primary key with auto-generation
- created_at timestamp with auto-set on insert
- updated_at timestamp with auto-update on change
"""
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import TypeDecorator, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID as PG_UUID


def utc_now() -> datetime:
    """Return current UTC datetime with timezone info.

    Returns:
        Current datetime in UTC with timezone info.
    """
    return datetime.now(timezone.utc)


class GUID(TypeDecorator):
    """Platform-independent GUID type.

    Uses PostgreSQL's UUID type when available, otherwise uses
    String(36) with UUID conversion for SQLite compatibility.
    """

    impl = String(36)
    cache_ok = True

    def load_dialect_impl(self, dialect: Any) -> Any:
        """Return the dialect-specific type."""
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PG_UUID(as_uuid=True))
        return dialect.type_descriptor(String(36))

    def process_bind_param(self, value: Any, dialect: Any) -> Any:
        """Convert UUID to string for storage."""
        if value is None:
            return value
        if dialect.name == "postgresql":
            return value
        if isinstance(value, uuid.UUID):
            return str(value)
        return value

    def process_result_value(self, value: Any, dialect: Any) -> Any:
        """Convert string back to UUID on retrieval."""
        if value is None:
            return value
        if isinstance(value, uuid.UUID):
            return value
        return uuid.UUID(value)


class BaseModel(DeclarativeBase):
    """Base model class providing common fields for all models.

    Attributes:
        id: UUID primary key, auto-generated on create.
        created_at: Timestamp when record was created.
        updated_at: Timestamp when record was last updated.
    """

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4,
    )

    created_at: Mapped[datetime] = mapped_column(
        default=utc_now,
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )
