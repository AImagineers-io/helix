"""Mixins for Helix models.

Provides reusable functionality:
- SoftDeleteMixin: Soft delete pattern with deleted_at timestamp
"""
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Mapped, mapped_column, declared_attr


class SoftDeleteMixin:
    """Mixin providing soft delete functionality.

    Adds a deleted_at timestamp field that marks records as deleted
    without physically removing them from the database.

    Attributes:
        deleted_at: Timestamp when record was soft deleted (None if active).

    Properties:
        is_deleted: Returns True if record is soft deleted.

    Class Methods:
        active(): Returns a filter clause for non-deleted records.
    """

    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        nullable=True,
        default=None,
    )

    @property
    def is_deleted(self) -> bool:
        """Check if this record has been soft deleted.

        Returns:
            True if deleted_at is set, False otherwise.
        """
        return self.deleted_at is not None

    @classmethod
    def active(cls):
        """Get filter clause for active (non-deleted) records.

        Use in queries to exclude soft-deleted records:
            session.query(Model).filter(Model.active())

        Returns:
            SQLAlchemy filter clause.
        """
        return cls.deleted_at.is_(None)
