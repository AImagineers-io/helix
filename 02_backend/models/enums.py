"""Enums for Helix models.

Provides status and type enumerations:
- QAStatus: Status for QA pair lifecycle
"""
import enum


class QAStatus(str, enum.Enum):
    """Status enum for QA pair lifecycle.

    Values:
        DRAFT: Initial state, not visible to users.
        ACTIVE: Published and available for RAG retrieval.
        ARCHIVED: Removed from active use but preserved for history.
    """

    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"
