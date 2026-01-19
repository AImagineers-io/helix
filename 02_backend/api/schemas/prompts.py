"""Pydantic schemas for Prompt Management API."""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field


class PromptVersionResponse(BaseModel):
    """Response model for prompt version."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    template_id: int
    content: str
    version_number: int
    is_active: bool
    created_at: datetime
    created_by: Optional[str] = None
    change_notes: Optional[str] = None


class PromptTemplateResponse(BaseModel):
    """Response model for prompt template."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    prompt_type: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    versions: List[PromptVersionResponse] = []


class PromptTemplateListResponse(BaseModel):
    """Response model for listing templates (without versions)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    prompt_type: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class CreatePromptRequest(BaseModel):
    """Request model for creating a prompt template."""

    name: str = Field(..., min_length=1, max_length=255)
    prompt_type: str = Field(..., min_length=1, max_length=50)
    content: str = Field(..., min_length=1)
    description: Optional[str] = None
    created_by: Optional[str] = None


class UpdatePromptRequest(BaseModel):
    """Request model for updating a prompt template."""

    content: Optional[str] = None
    description: Optional[str] = None
    created_by: Optional[str] = None
    change_notes: Optional[str] = None


class DeletePromptResponse(BaseModel):
    """Response model for delete operation."""

    message: str
