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
    VersionConflictError,
)
from api.auth import verify_api_key
from api.schemas.prompts import (
    PromptTemplateResponse,
    PromptTemplateListResponse,
    CreatePromptRequest,
    UpdatePromptRequest,
    DeletePromptResponse,
    PreviewPromptRequest,
    PreviewPromptResponse,
    PromptAuditLogResponse,
)
from services.prompt_audit import PromptAuditService
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
    api_key: str = Depends(verify_api_key),
):
    """Create a new prompt template.

    Args:
        request: Prompt creation request.
        db: Database session.
        api_key: Validated API key.

    Returns:
        Created prompt template with version.

    Raises:
        HTTPException 400: If template name already exists.
    """
    service = PromptService(db)
    audit_service = PromptAuditService(db)

    try:
        template = service.create_template(
            name=request.name,
            prompt_type=request.prompt_type,
            content=request.content,
            description=request.description,
            created_by=request.created_by,
        )
        logger.info(f"Created prompt template: {template.name} (ID: {template.id})")

        # Log audit
        audit_service.log_create(
            template_id=template.id,
            template_name=template.name,
            api_key=api_key,
        )

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
    description="Update prompt content (creates new version) or metadata. Requires edit_version for optimistic locking.",
)
def update_prompt(
    template_id: int,
    request: UpdatePromptRequest,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key),
):
    """Update a prompt template with optimistic locking.

    If content is provided, creates a new version.
    If only metadata is provided, updates template without new version.
    Requires edit_version to prevent concurrent update conflicts.

    Args:
        template_id: Template ID.
        request: Update request with edit_version.
        db: Database session.
        api_key: Validated API key.

    Returns:
        Updated prompt template.

    Raises:
        HTTPException 400: If edit_version not provided.
        HTTPException 404: If template not found.
        HTTPException 409: If version conflict (concurrent edit).
    """
    # Validate edit_version is provided
    if request.edit_version is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="edit_version is required for updates. "
                   "Get the current version from GET /prompts/{id}.",
        )

    service = PromptService(db)
    audit_service = PromptAuditService(db)

    try:
        template = service.update_template(
            template_id=template_id,
            edit_version=request.edit_version,
            content=request.content,
            description=request.description,
            created_by=request.created_by,
            change_notes=request.change_notes,
        )
        logger.info(f"Updated prompt template: {template.name} (ID: {template.id})")

        # Log audit
        active_version = template.active_version
        version_num = active_version.version_number if active_version else None
        audit_service.log_update(
            template_id=template.id,
            version_number=version_num,
            api_key=api_key,
        )

        return template

    except PromptNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except VersionConflictError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
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
    api_key: str = Depends(verify_api_key),
):
    """Delete a prompt template (soft delete).

    Args:
        template_id: Template ID.
        db: Database session.
        api_key: Validated API key.

    Returns:
        Deletion confirmation message.

    Raises:
        HTTPException 404: If template not found.
    """
    service = PromptService(db)
    audit_service = PromptAuditService(db)

    try:
        # Get template name before deletion
        template = service.get_template(template_id)
        template_name = template.name

        service.delete_template(template_id)
        logger.info(f"Deleted prompt template ID: {template_id}")

        # Log audit
        audit_service.log_delete(
            template_id=template_id,
            template_name=template_name,
            api_key=api_key,
        )

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
    api_key: str = Depends(verify_api_key),
):
    """Publish (activate) a specific version of a template.

    Deactivates the currently active version and activates the specified one.

    Args:
        template_id: Template ID.
        request: Publish request with version number.
        db: Database session.
        api_key: Validated API key.

    Returns:
        Activated version details.

    Raises:
        HTTPException 404: If template or version not found.
    """
    service = PromptService(db)
    audit_service = PromptAuditService(db)

    try:
        version = service.publish_version(
            template_id=template_id,
            version_number=request.version_number,
        )
        logger.info(
            f"Published version {version.version_number} for template ID {template_id}"
        )

        # Log audit
        audit_service.log_publish(
            template_id=template_id,
            version_number=request.version_number,
            api_key=api_key,
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
    api_key: str = Depends(verify_api_key),
):
    """Rollback to the previous version of a template.

    Args:
        template_id: Template ID.
        db: Database session.
        api_key: Validated API key.

    Returns:
        Activated previous version details.

    Raises:
        HTTPException 400: If already at version 1.
        HTTPException 404: If template not found.
    """
    service = PromptService(db)
    audit_service = PromptAuditService(db)

    try:
        # Get current version before rollback
        template = service.get_template(template_id)
        active = template.active_version
        from_version = active.version_number if active else 0

        version = service.rollback(template_id=template_id)
        logger.info(
            f"Rolled back to version {version.version_number} for template ID {template_id}"
        )

        # Log audit
        audit_service.log_rollback(
            template_id=template_id,
            from_version=from_version,
            to_version=version.version_number,
            api_key=api_key,
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


@router.post(
    "/{template_id}/preview",
    response_model=PreviewPromptResponse,
    summary="Preview prompt with context",
    description="Preview a prompt template with sample context variables substituted.",
)
def preview_prompt(
    template_id: int,
    request: PreviewPromptRequest,
    db: Session = Depends(get_db),
):
    """Preview a prompt with variables substituted.

    Renders the prompt template by substituting provided context variables.
    Returns the original content, rendered content, and list of variables found.

    Args:
        template_id: Template ID.
        request: Preview request with context variables and optional version.
        db: Database session.

    Returns:
        Preview response with original, rendered content and variables.

    Raises:
        HTTPException 404: If template or version not found.
    """
    service = PromptService(db)

    try:
        result = service.preview(
            template_id=template_id,
            context=request.context,
            version_number=request.version_number,
        )
        return PreviewPromptResponse(
            original=result["original"],
            rendered=result["rendered"],
            variables=result["variables"],
        )

    except (PromptNotFoundError, VersionNotFoundError) as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get(
    "/{template_id}/audit",
    response_model=List[PromptAuditLogResponse],
    summary="Get audit logs",
    description="Get audit log history for a prompt template.",
)
def get_audit_logs(
    template_id: int,
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of logs"),
    db: Session = Depends(get_db),
):
    """Get audit logs for a prompt template.

    Returns all recorded actions for the template, ordered by timestamp descending.

    Args:
        template_id: Template ID.
        limit: Maximum number of logs to return (default 100, max 1000).
        db: Database session.

    Returns:
        List of audit log entries.

    Raises:
        HTTPException 404: If template not found.
    """
    service = PromptService(db)
    audit_service = PromptAuditService(db)

    try:
        # Verify template exists
        service.get_template(template_id)

        # Get audit logs
        logs = audit_service.get_audit_logs(template_id, limit=limit)
        return logs

    except PromptNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
