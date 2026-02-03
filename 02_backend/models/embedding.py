"""Embedding model for Helix knowledge base.

Stores vector embeddings for semantic search.
Uses JSON type by default for SQLite compatibility.
For PostgreSQL with pgvector, the migration creates the proper Vector column.
"""
from typing import Optional, List, TYPE_CHECKING
import uuid

from sqlalchemy import String, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import BaseModel, GUID


if TYPE_CHECKING:
    from models.qa_pair import QAPair


class Embedding(BaseModel):
    """Vector embedding for a QA pair.

    Stores the vector representation of a QA pair's question for semantic search.
    Uses JSON storage by default (SQLite compatible), with pgvector Vector type
    available via migration for PostgreSQL.

    Attributes:
        qa_pair_id: Foreign key to the associated QAPair (unique, one-to-one).
        vector: The embedding vector (1536 dimensions for OpenAI text-embedding-3-small).
        model_version: Name/version of the embedding model used.
        qa_pair: Relationship to the parent QAPair.
    """

    __tablename__ = "embedding"

    qa_pair_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey("qa_pair.id", ondelete="CASCADE"),
        unique=True,
        index=True,
        nullable=False,
    )

    # Vector storage - JSON for SQLite, Vector type added via migration for PostgreSQL
    vector: Mapped[List[float]] = mapped_column(
        JSON,
        nullable=False,
    )

    model_version: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    # Relationship back to QAPair
    qa_pair: Mapped["QAPair"] = relationship(
        "QAPair",
        back_populates="embedding",
    )

    def __repr__(self) -> str:
        """Return string representation."""
        return f"<Embedding(id={self.id}, qa_pair_id={self.qa_pair_id}, model={self.model_version})>"
