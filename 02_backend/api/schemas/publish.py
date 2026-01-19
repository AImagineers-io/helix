"""Pydantic schemas for publish and rollback endpoints."""
from pydantic import BaseModel, Field


class PublishVersionRequest(BaseModel):
    """Request model for publishing a version."""

    version_number: int = Field(..., ge=1, description="Version number to activate")


class PublishVersionResponse(BaseModel):
    """Response model for publish operation."""

    id: int
    template_id: int
    version_number: int
    is_active: bool
    message: str
