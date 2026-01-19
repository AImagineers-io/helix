"""Prompt Management API router.

Provides REST endpoints for managing prompt templates and versions:
- GET /prompts - List all templates
- POST /prompts - Create template
- GET /prompts/{id} - Get template with versions
- PUT /prompts/{id} - Update template
- DELETE /prompts/{id} - Delete template (soft delete)
"""
import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from database.connection import get_db
from services.prompt_service import (
    PromptService,
    PromptNotFoundError,
    VersionNotFoundError,
)
from api.auth import verify_api_key
from api.schemas.prompts import (
    PromptTemplateResponse,
    PromptTemplateListResponse,
    CreatePromptRequest,
    UpdatePromptRequest,
    DeletePromptResponse,
)
from api.schemas.publish import (
    PublishVersionRequest,
    PublishVersionResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/prompts",
    tags=["prompts"],
    dependencies=[Depends(verify_api_key)],
)


@router.get(
    "",
    response_model=List[PromptTemplateListResponse],
    summary="List prompt templates",
    description="Get all prompt templates, optionally filtered by type.",
)
def list_prompts(
    prompt_type: Optional[str] = Query(None, description="Filter by prompt type"),
    db: Session = Depends(get_db),
):
    """List all prompt templates.

    Args:
        prompt_type: Optional filter by prompt type.
        db: Database session.

    Returns:
        List of prompt templates (without version details).
    """
    service = PromptService(db)
    templates = service.list_templates(prompt_type=prompt_type)
    return templates


@router.post(
    "",
    response_model=PromptTemplateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create prompt template",
    description="Create a new prompt template with initial version.",
)
def create_prompt(
    request: CreatePromptRequest,
    db: Session = Depends(get_db),
):
    """Create a new prompt template.

    Args:
        request: Prompt creation request.
        db: Database session.

    Returns:
        Created prompt template with version.

    Raises:
        HTTPException 400: If template name already exists.
    """
    service = PromptService(db)

    try:
        template = service.create_template(
            name=request.name,
            prompt_type=request.prompt_type,
            content=request.content,
            description=request.description,
            created_by=request.created_by,
        )
        logger.info(f"Created prompt template: {template.name} (ID: {template.id})")
        return template

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get(
    "/{template_id}",
    response_model=PromptTemplateResponse,
    summary="Get prompt template",
    description="Get a prompt template by ID including all versions.",
)
def get_prompt(
    template_id: int,
    db: Session = Depends(get_db),
):
    """Get a prompt template by ID.

    Args:
        template_id: Template ID.
        db: Database session.

    Returns:
        Prompt template with all versions.

    Raises:
        HTTPException 404: If template not found.
    """
    service = PromptService(db)

    try:
        template = service.get_template(template_id)
        return template

    except PromptNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.put(
    "/{template_id}",
    response_model=PromptTemplateResponse,
    summary="Update prompt template",
    description="Update prompt content (creates new version) or metadata.",
)
def update_prompt(
    template_id: int,
    request: UpdatePromptRequest,
    db: Session = Depends(get_db),
):
    """Update a prompt template.

    If content is provided, creates a new version.
    If only metadata is provided, updates template without new version.

    Args:
        template_id: Template ID.
        request: Update request.
        db: Database session.

    Returns:
        Updated prompt template.

    Raises:
        HTTPException 404: If template not found.
    """
    service = PromptService(db)

    try:
        template = service.update_template(
            template_id=template_id,
            content=request.content,
            description=request.description,
            created_by=request.created_by,
            change_notes=request.change_notes,
        )
        logger.info(f"Updated prompt template: {template.name} (ID: {template.id})")
        return template

    except PromptNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.delete(
    "/{template_id}",
    response_model=DeletePromptResponse,
    summary="Delete prompt template",
    description="Soft delete a prompt template.",
)
def delete_prompt(
    template_id: int,
    db: Session = Depends(get_db),
):
    """Delete a prompt template (soft delete).

    Args:
        template_id: Template ID.
        db: Database session.

    Returns:
        Deletion confirmation message.

    Raises:
        HTTPException 404: If template not found.
    """
    service = PromptService(db)

    try:
        service.delete_template(template_id)
        logger.info(f"Deleted prompt template ID: {template_id}")
        return DeletePromptResponse(message="Prompt template deleted successfully")

    except PromptNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.post(
    "/{template_id}/publish",
    response_model=PublishVersionResponse,
    summary="Publish prompt version",
    description="Activate a specific version of a prompt template.",
)
def publish_version(
    template_id: int,
    request: PublishVersionRequest,
    db: Session = Depends(get_db),
):
    """Publish (activate) a specific version of a template.

    Deactivates the currently active version and activates the specified one.

    Args:
        template_id: Template ID.
        request: Publish request with version number.
        db: Database session.

    Returns:
        Activated version details.

    Raises:
        HTTPException 404: If template or version not found.
    """
    service = PromptService(db)

    try:
        version = service.publish_version(
            template_id=template_id,
            version_number=request.version_number,
        )
        logger.info(
            f"Published version {version.version_number} for template ID {template_id}"
        )
        return PublishVersionResponse(
            id=version.id,
            template_id=version.template_id,
            version_number=version.version_number,
            is_active=version.is_active,
            message=f"Version {version.version_number} is now active",
        )

    except (PromptNotFoundError, VersionNotFoundError) as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.post(
    "/{template_id}/rollback",
    response_model=PublishVersionResponse,
    summary="Rollback prompt version",
    description="Rollback to the previous version of a prompt template.",
)
def rollback_version(
    template_id: int,
    db: Session = Depends(get_db),
):
    """Rollback to the previous version of a template.

    Args:
        template_id: Template ID.
        db: Database session.

    Returns:
        Activated previous version details.

    Raises:
        HTTPException 400: If already at version 1.
        HTTPException 404: If template not found.
    """
    service = PromptService(db)

    try:
        version = service.rollback(template_id=template_id)
        logger.info(
            f"Rolled back to version {version.version_number} for template ID {template_id}"
        )
        return PublishVersionResponse(
            id=version.id,
            template_id=version.template_id,
            version_number=version.version_number,
            is_active=version.is_active,
            message=f"Rolled back to version {version.version_number}",
        )

    except PromptNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
