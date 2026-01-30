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
    edit_version: int
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
    edit_version: int
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
    """Request model for updating a prompt template.

    Attributes:
        edit_version: Required for optimistic locking. Must match current version.
        content: Optional new prompt content (creates new version if provided).
        description: Optional new description.
        created_by: Optional updater identifier.
        change_notes: Optional notes about the changes.
    """

    edit_version: Optional[int] = Field(
        None,
        description="Current edit version for optimistic locking. Required for updates."
    )
    content: Optional[str] = None
    description: Optional[str] = None
    created_by: Optional[str] = None
    change_notes: Optional[str] = None


class DeletePromptResponse(BaseModel):
    """Response model for delete operation."""

    message: str


class PreviewPromptRequest(BaseModel):
    """Request model for previewing a prompt with context."""

    context: dict[str, str] = Field(
        default_factory=dict,
        description="Variables to substitute in the prompt template."
    )
    version_number: Optional[int] = Field(
        None,
        description="Specific version to preview. Uses active version if not specified."
    )


class PreviewPromptResponse(BaseModel):
    """Response model for prompt preview."""

    original: str = Field(..., description="Original prompt content")
    rendered: str = Field(..., description="Rendered prompt with variables substituted")
    variables: List[str] = Field(
        default_factory=list,
        description="List of variable names found in the template"
    )


class PromptAuditLogResponse(BaseModel):
    """Response model for prompt audit log entry."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    template_id: int
    action: str
    admin_key_hash: Optional[str] = None
    timestamp: datetime
    details: Optional[dict] = None
