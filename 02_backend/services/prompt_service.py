"""Prompt management service.

Provides business logic for managing prompt templates and versions:
- CRUD operations for templates
- Version management (create, activate, rollback)
- Content retrieval for active prompts
- Cache-aware operations
- Fallback behavior for missing prompts
"""
import logging
from datetime import datetime, timezone
from typing import Optional, List, TYPE_CHECKING

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from database.models import PromptTemplate, PromptVersion
from core.constants import PromptType, DEFAULT_PROMPTS

if TYPE_CHECKING:
    from services.prompt_cache import PromptCacheService

logger = logging.getLogger(__name__)


class PromptNotFoundError(Exception):
    """Raised when a prompt template is not found."""
    pass


class VersionNotFoundError(Exception):
    """Raised when a prompt version is not found."""
    pass


class VersionConflictError(Exception):
    """Raised when optimistic locking detects a version conflict."""
    pass


class PromptService:
    """Service for managing prompt templates and versions."""

    def __init__(self, db: Session):
        """Initialize service with database session.

        Args:
            db: SQLAlchemy database session.
        """
        self.db = db

    def create_template(
        self,
        name: str,
        prompt_type: str,
        content: str,
        description: Optional[str] = None,
        created_by: Optional[str] = None,
    ) -> PromptTemplate:
        """Create a new prompt template with initial version.

        Args:
            name: Unique template name.
            prompt_type: Type of prompt (system, retrieval, moderation, etc.).
            content: Initial prompt content.
            description: Optional template description.
            created_by: Optional creator identifier.

        Returns:
            Created PromptTemplate with active version.

        Raises:
            ValueError: If template name already exists.
        """
        # Check for duplicate name
        existing = self.get_template_by_name(name)
        if existing:
            raise ValueError(f"Template with name '{name}' already exists")

        # Create template
        template = PromptTemplate(
            name=name,
            prompt_type=prompt_type,
            description=description,
        )
        self.db.add(template)
        self.db.flush()  # Get ID for version

        # Create initial version
        version = PromptVersion(
            template_id=template.id,
            content=content,
            version_number=1,
            is_active=True,
            created_by=created_by,
        )
        self.db.add(version)
        self.db.commit()
        self.db.refresh(template)

        return template

    def get_template(
        self,
        template_id: int,
        include_deleted: bool = False,
    ) -> PromptTemplate:
        """Get a template by ID.

        Args:
            template_id: Template ID.
            include_deleted: Whether to include soft-deleted templates.

        Returns:
            PromptTemplate instance.

        Raises:
            PromptNotFoundError: If template not found.
        """
        query = self.db.query(PromptTemplate).filter(
            PromptTemplate.id == template_id
        )

        if not include_deleted:
            query = query.filter(PromptTemplate.deleted_at.is_(None))

        template = query.first()

        if not template:
            raise PromptNotFoundError(f"Template with ID {template_id} not found")

        return template

    def get_template_by_name(self, name: str) -> Optional[PromptTemplate]:
        """Get a template by name.

        Args:
            name: Template name.

        Returns:
            PromptTemplate if found, None otherwise.
        """
        return self.db.query(PromptTemplate).filter(
            PromptTemplate.name == name,
            PromptTemplate.deleted_at.is_(None),
        ).first()

    def list_templates(
        self,
        prompt_type: Optional[str] = None,
        include_deleted: bool = False,
    ) -> List[PromptTemplate]:
        """List all templates, optionally filtered by type.

        Args:
            prompt_type: Optional filter by prompt type.
            include_deleted: Whether to include soft-deleted templates.

        Returns:
            List of PromptTemplate instances.
        """
        query = self.db.query(PromptTemplate)

        if not include_deleted:
            query = query.filter(PromptTemplate.deleted_at.is_(None))

        if prompt_type:
            query = query.filter(PromptTemplate.prompt_type == prompt_type)

        return query.order_by(PromptTemplate.name).all()

    def update_template(
        self,
        template_id: int,
        edit_version: int,
        content: Optional[str] = None,
        description: Optional[str] = None,
        created_by: Optional[str] = None,
        change_notes: Optional[str] = None,
    ) -> PromptTemplate:
        """Update a template's content or metadata with optimistic locking.

        If content is provided, creates a new version.
        If only metadata is provided, updates template without new version.

        Args:
            template_id: Template ID to update.
            edit_version: Current edit_version for optimistic locking.
            content: Optional new prompt content (creates new version).
            description: Optional new description.
            created_by: Optional updater identifier.
            change_notes: Optional notes about the changes.

        Returns:
            Updated PromptTemplate.

        Raises:
            PromptNotFoundError: If template not found.
            VersionConflictError: If edit_version doesn't match current version.
        """
        template = self.get_template(template_id)

        # Check optimistic locking version
        if template.edit_version != edit_version:
            raise VersionConflictError(
                f"Version conflict: expected version {edit_version}, "
                f"but current version is {template.edit_version}. "
                "Another user may have modified this template."
            )

        # Update metadata if provided
        if description is not None:
            template.description = description
            template.updated_at = datetime.now(timezone.utc)

        # Create new version if content changed
        if content is not None:
            # Deactivate current active version
            active = template.active_version
            if active:
                active.is_active = False

            # Get next version number
            max_version = max(v.version_number for v in template.versions) if template.versions else 0
            next_version = max_version + 1

            # Create new version
            new_version = PromptVersion(
                template_id=template.id,
                content=content,
                version_number=next_version,
                is_active=True,
                created_by=created_by,
                change_notes=change_notes,
            )
            self.db.add(new_version)
            template.updated_at = datetime.now(timezone.utc)

        # Increment edit_version for optimistic locking
        template.edit_version += 1

        self.db.commit()
        self.db.refresh(template)
        return template

    def delete_template(self, template_id: int) -> None:
        """Soft delete a template.

        Args:
            template_id: Template ID to delete.

        Raises:
            PromptNotFoundError: If template not found.
        """
        template = self.get_template(template_id)
        template.deleted_at = datetime.now(timezone.utc)
        self.db.commit()

    def get_version(
        self,
        template_id: int,
        version_number: int,
    ) -> PromptVersion:
        """Get a specific version of a template.

        Args:
            template_id: Template ID.
            version_number: Version number to retrieve.

        Returns:
            PromptVersion instance.

        Raises:
            VersionNotFoundError: If version not found.
        """
        version = self.db.query(PromptVersion).filter(
            PromptVersion.template_id == template_id,
            PromptVersion.version_number == version_number,
        ).first()

        if not version:
            raise VersionNotFoundError(
                f"Version {version_number} not found for template {template_id}"
            )

        return version

    def list_versions(self, template_id: int) -> List[PromptVersion]:
        """List all versions for a template.

        Args:
            template_id: Template ID.

        Returns:
            List of PromptVersion instances, ordered by version number descending.
        """
        return self.db.query(PromptVersion).filter(
            PromptVersion.template_id == template_id
        ).order_by(PromptVersion.version_number.desc()).all()

    def get_active_content(self, template_name: str) -> Optional[str]:
        """Get the active prompt content for a template by name.

        Args:
            template_name: Template name.

        Returns:
            Active prompt content if found, None otherwise.
        """
        template = self.get_template_by_name(template_name)
        if not template:
            return None

        active = template.active_version
        if not active:
            return None

        return active.content

    def publish_version(
        self,
        template_id: int,
        version_number: int,
    ) -> PromptVersion:
        """Activate a specific version of a template.

        Deactivates the currently active version and activates the specified one.

        Args:
            template_id: Template ID.
            version_number: Version number to activate.

        Returns:
            Activated PromptVersion.

        Raises:
            VersionNotFoundError: If version not found.
        """
        template = self.get_template(template_id)

        # Deactivate current active version
        for version in template.versions:
            if version.is_active:
                version.is_active = False

        # Activate target version
        target_version = self.get_version(template_id, version_number)
        target_version.is_active = True

        self.db.commit()
        self.db.refresh(target_version)

        return target_version

    def rollback(self, template_id: int) -> PromptVersion:
        """Rollback to the previous version of a template.

        Args:
            template_id: Template ID.

        Returns:
            Activated previous version.

        Raises:
            ValueError: If already at version 1 or no active version.
            PromptNotFoundError: If template not found.
        """
        template = self.get_template(template_id)

        active = template.active_version
        if not active:
            raise ValueError("No active version to rollback from")

        if active.version_number == 1:
            raise ValueError("Cannot rollback from version 1")

        previous_version_number = active.version_number - 1

        return self.publish_version(template_id, previous_version_number)

    def preview(
        self,
        template_id: int,
        context: dict[str, str],
        version_number: Optional[int] = None,
    ) -> dict:
        """Preview a prompt with variables substituted.

        Args:
            template_id: Template ID.
            context: Dictionary of variable names to values.
            version_number: Optional specific version to preview.
                           Uses active version if not specified.

        Returns:
            Dictionary with 'original', 'rendered', and 'variables' keys.

        Raises:
            PromptNotFoundError: If template not found.
            VersionNotFoundError: If specified version not found.
        """
        import re

        template = self.get_template(template_id)

        # Get the version content
        if version_number is not None:
            version = self.get_version(template_id, version_number)
            content = version.content
        else:
            active = template.active_version
            if not active:
                raise ValueError("No active version found")
            content = active.content

        # Extract variable names from template
        variable_pattern = re.compile(r'\{([a-zA-Z_][a-zA-Z0-9_]*)\}')
        variables = list(set(variable_pattern.findall(content)))

        # Render by substituting variables
        rendered = content
        for var_name, var_value in context.items():
            rendered = rendered.replace(f"{{{var_name}}}", str(var_value))

        return {
            "original": content,
            "rendered": rendered,
            "variables": variables,
        }

    def get_active_content_with_cache(
        self,
        template_name: str,
        cache: "PromptCacheService",
    ) -> Optional[str]:
        """Get active prompt content with caching.

        Uses read-through caching: tries cache first, falls back to DB,
        then caches the result.

        Args:
            template_name: Template name to retrieve.
            cache: Cache service instance.

        Returns:
            Active prompt content if found, None otherwise.
        """
        template = self.get_template_by_name(template_name)
        if not template:
            return None

        prompt_type = template.prompt_type

        def fetch_from_db() -> Optional[str]:
            return self.get_active_content(template_name)

        return cache.get_or_fetch(prompt_type, fetch_from_db)

    def publish_version_with_cache(
        self,
        template_id: int,
        version_number: int,
        cache: "PromptCacheService",
    ) -> PromptVersion:
        """Publish a version and invalidate cache.

        Args:
            template_id: Template ID.
            version_number: Version number to publish.
            cache: Cache service instance.

        Returns:
            Published version.
        """
        # Get template to know prompt_type before publishing
        template = self.get_template(template_id)
        prompt_type = template.prompt_type

        # Publish the version
        version = self.publish_version(template_id, version_number)

        # Invalidate cache
        cache.invalidate_prompt(prompt_type)

        return version

    def get_active_content_with_fallback(
        self,
        template_name: str,
        prompt_type: Optional[PromptType] = None,
    ) -> Optional[str]:
        """Get active prompt content with fallback to defaults.

        This method is designed to never fail for missing prompts.
        If the prompt is not found in the database, it returns the
        default content for the given prompt type.

        Args:
            template_name: Template name to retrieve.
            prompt_type: Optional prompt type for fallback.
                        Required to get fallback content.

        Returns:
            Prompt content from DB or fallback default.
            None only if prompt_type is not provided and template not found.
        """
        # Try to get from database first
        content = self.get_active_content(template_name)
        if content is not None:
            return content

        # Template not found - use fallback if prompt_type provided
        if prompt_type is not None:
            logger.warning(
                f"Prompt '{template_name}' not found in database. "
                f"Using fallback default for type '{prompt_type.value}'."
            )
            return DEFAULT_PROMPTS.get(prompt_type)

        # No prompt_type provided, can't determine fallback
        return None
