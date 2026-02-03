"""Helix models package.

This package contains SQLAlchemy models for the knowledge base:
- BaseModel: Base class with common fields (id, created_at, updated_at)
- SoftDeleteMixin: Mixin for soft delete functionality
- QAPair: Question-answer pairs for the knowledge base
- Embedding: Vector embeddings for semantic search
- QAStatus: Status enum for QA pair lifecycle
"""
from models.base import BaseModel
from models.mixins import SoftDeleteMixin
from models.enums import QAStatus
from models.qa_pair import QAPair
from models.embedding import Embedding

__all__ = [
    "BaseModel",
    "SoftDeleteMixin",
    "QAStatus",
    "QAPair",
    "Embedding",
]
