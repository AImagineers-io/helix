"""QAPair model for Helix knowledge base.

Stores question-answer pairs for RAG retrieval.
"""
from typing import Optional, List, TYPE_CHECKING

from sqlalchemy import Text, String, JSON, Enum, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import BaseModel
from models.mixins import SoftDeleteMixin
from models.enums import QAStatus


if TYPE_CHECKING:
    from models.embedding import Embedding


class QAPair(BaseModel, SoftDeleteMixin):
    """Question-Answer pair for the knowledge base.

    Stores content that can be retrieved via semantic search for RAG responses.

    Attributes:
        question: The question text (indexed for search).
        answer: The answer text.
        category: Optional category for organization (indexed).
        tags: JSON array of tags for filtering.
        status: Lifecycle status (DRAFT, ACTIVE, ARCHIVED).
        embedding: One-to-one relationship to Embedding.
    """

    __tablename__ = "qa_pair"

    question: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        index=True,
    )

    answer: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    category: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )

    tags: Mapped[List] = mapped_column(
        JSON,
        default=list,
        nullable=False,
    )

    status: Mapped[QAStatus] = mapped_column(
        Enum(QAStatus),
        default=QAStatus.DRAFT,
        nullable=False,
        index=True,
    )

    # Relationship to Embedding (one-to-one)
    embedding: Mapped[Optional["Embedding"]] = relationship(
        "Embedding",
        back_populates="qa_pair",
        cascade="all, delete-orphan",
        uselist=False,
    )

    def __repr__(self) -> str:
        """Return string representation."""
        return f"<QAPair(id={self.id}, status={self.status.value}, question={self.question[:50]}...)>"
