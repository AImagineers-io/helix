"""
Prompt audit logging service.

Provides audit trail functionality for prompt management operations.
"""
import hashlib
import logging
from datetime import datetime, timezone
from typing import Optional, List, Any

from sqlalchemy.orm import Session

from database.models import PromptAuditLog

logger = logging.getLogger(__name__)


class PromptAuditService:
    """Service for managing prompt audit logs.

    Records all modifications to prompt templates for debugging,
    compliance, and accountability.

    Actions tracked:
    - create: New template created
    - update: Template content or metadata updated
    - publish: Version activated
    - rollback: Rolled back to previous version
    - delete: Template deleted
    """

    def __init__(self, db: Session):
        """Initialize service with database session.

        Args:
            db: SQLAlchemy database session.
        """
        self.db = db

    @staticmethod
    def hash_api_key(api_key: str) -> str:
        """Hash API key for storage in audit log.

        Uses SHA-256 to create a non-reversible hash for tracking
        which admin made changes without storing the actual key.

        Args:
            api_key: Plain text API key.

        Returns:
            SHA-256 hash of the API key.
        """
        return hashlib.sha256(api_key.encode()).hexdigest()[:16]

    def log_action(
        self,
        template_id: int,
        action: str,
        api_key: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
    ) -> PromptAuditLog:
        """Log an audit action.

        Args:
            template_id: ID of the affected template.
            action: Action type (create, update, publish, rollback, delete).
            api_key: Optional API key of the admin making the change.
            details: Optional additional details about the action.

        Returns:
            Created PromptAuditLog record.
        """
        admin_key_hash = self.hash_api_key(api_key) if api_key else None

        log = PromptAuditLog(
            template_id=template_id,
            action=action,
            admin_key_hash=admin_key_hash,
            timestamp=datetime.now(timezone.utc),
            details=details,
        )
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)

        logger.info(
            f"Audit: {action} on template {template_id} "
            f"by {admin_key_hash or 'unknown'}"
        )

        return log

    def log_create(
        self,
        template_id: int,
        template_name: str,
        api_key: Optional[str] = None,
    ) -> PromptAuditLog:
        """Log template creation.

        Args:
            template_id: ID of the created template.
            template_name: Name of the template.
            api_key: Optional API key of the creator.

        Returns:
            Created audit log.
        """
        return self.log_action(
            template_id=template_id,
            action="create",
            api_key=api_key,
            details={"template_name": template_name},
        )

    def log_update(
        self,
        template_id: int,
        version_number: Optional[int] = None,
        api_key: Optional[str] = None,
    ) -> PromptAuditLog:
        """Log template update.

        Args:
            template_id: ID of the updated template.
            version_number: New version number if content was changed.
            api_key: Optional API key of the updater.

        Returns:
            Created audit log.
        """
        details = {}
        if version_number is not None:
            details["new_version"] = version_number

        return self.log_action(
            template_id=template_id,
            action="update",
            api_key=api_key,
            details=details if details else None,
        )

    def log_publish(
        self,
        template_id: int,
        version_number: int,
        api_key: Optional[str] = None,
    ) -> PromptAuditLog:
        """Log version publish.

        Args:
            template_id: ID of the template.
            version_number: Version number being activated.
            api_key: Optional API key of the publisher.

        Returns:
            Created audit log.
        """
        return self.log_action(
            template_id=template_id,
            action="publish",
            api_key=api_key,
            details={"version_number": version_number},
        )

    def log_rollback(
        self,
        template_id: int,
        from_version: int,
        to_version: int,
        api_key: Optional[str] = None,
    ) -> PromptAuditLog:
        """Log version rollback.

        Args:
            template_id: ID of the template.
            from_version: Version being rolled back from.
            to_version: Version being rolled back to.
            api_key: Optional API key of the roller-backer.

        Returns:
            Created audit log.
        """
        return self.log_action(
            template_id=template_id,
            action="rollback",
            api_key=api_key,
            details={
                "from_version": from_version,
                "to_version": to_version,
            },
        )

    def log_delete(
        self,
        template_id: int,
        template_name: str,
        api_key: Optional[str] = None,
    ) -> PromptAuditLog:
        """Log template deletion.

        Args:
            template_id: ID of the deleted template.
            template_name: Name of the template being deleted.
            api_key: Optional API key of the deleter.

        Returns:
            Created audit log.
        """
        return self.log_action(
            template_id=template_id,
            action="delete",
            api_key=api_key,
            details={"template_name": template_name},
        )

    def get_audit_logs(
        self,
        template_id: int,
        limit: int = 100,
    ) -> List[PromptAuditLog]:
        """Get audit logs for a template.

        Args:
            template_id: ID of the template.
            limit: Maximum number of logs to return.

        Returns:
            List of audit logs, ordered by timestamp descending.
        """
        return self.db.query(PromptAuditLog).filter(
            PromptAuditLog.template_id == template_id
        ).order_by(
            PromptAuditLog.timestamp.desc()
        ).limit(limit).all()
