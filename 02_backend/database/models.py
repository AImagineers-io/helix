"""SQLAlchemy models for Helix database.

This module defines the database models for:
- PromptTemplate: Container for prompt templates with metadata.
- PromptVersion: Version history for prompt content with activation state.
- PromptAuditLog: Audit trail for prompt changes.
- AdminUser: Admin user accounts for authentication.
- Role: User roles for RBAC.
"""
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Boolean,
    ForeignKey, Index, TypeDecorator, JSON, Date, Numeric,
)
from sqlalchemy.orm import relationship

from database.connection import Base


def utc_now() -> datetime:
    """Return current UTC datetime with timezone info (ISO 8601 compliant).

    Returns:
        Current datetime in UTC with timezone info.
    """
    return datetime.now(timezone.utc)


class TZDateTime(TypeDecorator):
    """DateTime type that ensures timezone-aware UTC datetimes.

    Works with both SQLite (for testing) and PostgreSQL (for production).
    """

    impl = DateTime
    cache_ok = True

    def process_bind_param(self, value, dialect):
        """Process value before storing in database."""
        if value is not None:
            if value.tzinfo is None:
                value = value.replace(tzinfo=timezone.utc)
            else:
                value = value.astimezone(timezone.utc)
        return value

    def process_result_value(self, value, dialect):
        """Process value after reading from database."""
        if value is not None:
            if value.tzinfo is None:
                value = value.replace(tzinfo=timezone.utc)
        return value


class PromptTemplate(Base):
    """Prompt template model for storing configurable LLM prompts.

    Attributes:
        id: Primary key.
        name: Unique identifier for the template (e.g., 'system_prompt').
        description: Human-readable description of the template's purpose.
        prompt_type: Type of prompt (system, retrieval, moderation, etc.).
        edit_version: Optimistic locking version number, increments on each update.
        created_at: When the template was created.
        updated_at: When the template was last modified.
        deleted_at: Soft delete timestamp (NULL if not deleted).
        versions: Relationship to PromptVersion records.
    """

    __tablename__ = "prompt_templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    prompt_type = Column(String(50), nullable=False, index=True)
    edit_version = Column(Integer, default=1, nullable=False)

    created_at = Column(TZDateTime, default=utc_now, nullable=False)
    updated_at = Column(TZDateTime, default=utc_now, onupdate=utc_now, nullable=False)
    deleted_at = Column(TZDateTime, nullable=True, index=True)

    versions = relationship(
        "PromptVersion",
        back_populates="template",
        cascade="all, delete-orphan",
        order_by="PromptVersion.version_number.desc()",
    )

    def __repr__(self):
        return f"<PromptTemplate(id={self.id}, name={self.name}, type={self.prompt_type})>"

    @property
    def active_version(self):
        """Get the currently active version of this template."""
        for version in self.versions:
            if version.is_active:
                return version
        return None


class PromptVersion(Base):
    """Prompt version model for versioning prompt content.

    Attributes:
        id: Primary key.
        template_id: Foreign key to PromptTemplate.
        content: The actual prompt text content.
        version_number: Version number (increments with each new version).
        is_active: Whether this version is currently active.
        created_at: When this version was created.
        created_by: Who created this version (email/username).
        change_notes: Optional notes describing changes in this version.
        template: Relationship to parent PromptTemplate.
    """

    __tablename__ = "prompt_versions"

    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(
        Integer,
        ForeignKey("prompt_templates.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    content = Column(Text, nullable=False)
    version_number = Column(Integer, nullable=False)
    is_active = Column(Boolean, default=False, nullable=False, index=True)

    created_at = Column(TZDateTime, default=utc_now, nullable=False, index=True)
    created_by = Column(String(255), nullable=True)
    change_notes = Column(Text, nullable=True)

    template = relationship("PromptTemplate", back_populates="versions")

    __table_args__ = (
        Index(
            "ix_prompt_version_template_version",
            "template_id",
            "version_number",
            unique=True,
        ),
    )

    def __repr__(self):
        return (
            f"<PromptVersion(id={self.id}, template_id={self.template_id}, "
            f"v{self.version_number}, active={self.is_active})>"
        )


class PromptAuditLog(Base):
    """Audit log for tracking prompt changes.

    Records all modifications to prompt templates for debugging and compliance.

    Attributes:
        id: Primary key.
        template_id: Foreign key to PromptTemplate.
        action: Action type (create, update, publish, rollback, delete).
        admin_key_hash: Hashed API key of the user who made the change.
        timestamp: When the action occurred.
        details: JSON field with action-specific details.
    """

    __tablename__ = "prompt_audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(
        Integer,
        ForeignKey("prompt_templates.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    action = Column(String(50), nullable=False, index=True)
    admin_key_hash = Column(String(64), nullable=True)
    timestamp = Column(TZDateTime, default=utc_now, nullable=False, index=True)
    details = Column(JSON, nullable=True)

    template = relationship("PromptTemplate")

    def __repr__(self):
        return (
            f"<PromptAuditLog(id={self.id}, template_id={self.template_id}, "
            f"action={self.action})>"
        )


class DailyAggregate(Base):
    """Pre-computed daily analytics aggregates.

    Stores aggregated metrics per day for efficient analytics queries.
    Computed via scheduled job rather than on-demand calculation.

    Attributes:
        id: Primary key.
        date: The date this aggregate represents (unique).
        conversation_count: Number of conversations that day.
        message_count: Number of messages exchanged.
        avg_response_time_ms: Average response time in milliseconds.
        cost_total: Total cost incurred that day.
        created_at: When this aggregate was computed.
        updated_at: When this aggregate was last updated.
    """

    __tablename__ = "daily_aggregates"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, unique=True, nullable=False, index=True)
    conversation_count = Column(Integer, default=0, nullable=False)
    message_count = Column(Integer, default=0, nullable=False)
    avg_response_time_ms = Column(Integer, nullable=True)
    cost_total = Column(Numeric(10, 2), default=0, nullable=False)

    created_at = Column(TZDateTime, default=utc_now, nullable=False)
    updated_at = Column(TZDateTime, default=utc_now, onupdate=utc_now, nullable=False)

    def __repr__(self):
        return (
            f"<DailyAggregate(id={self.id}, date={self.date}, "
            f"conversations={self.conversation_count}, cost={self.cost_total})>"
        )


class AdminUser(Base):
    """Admin user model for authentication.

    Stores admin user credentials and metadata for JWT-based authentication.

    Attributes:
        id: Primary key.
        username: Unique username for login.
        email: User email address (unique).
        password_hash: Bcrypt hash of the user's password.
        is_active: Whether the user account is active.
        is_superuser: Whether the user has superuser privileges.
        role: User's role (for RBAC).
        mfa_secret: TOTP secret for MFA (optional).
        mfa_enabled: Whether MFA is enabled for this user.
        last_login: Timestamp of last successful login.
        failed_login_attempts: Count of consecutive failed login attempts.
        locked_until: Timestamp until which the account is locked (if any).
        created_at: When the user was created.
        updated_at: When the user was last modified.
    """

    __tablename__ = "admin_users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(255), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)

    is_active = Column(Boolean, default=True, nullable=False, index=True)
    is_superuser = Column(Boolean, default=False, nullable=False)
    role = Column(String(50), default="VIEWER", nullable=False, index=True)

    # MFA fields
    mfa_secret = Column(String(32), nullable=True)
    mfa_enabled = Column(Boolean, default=False, nullable=False)

    # Security fields
    last_login = Column(TZDateTime, nullable=True)
    failed_login_attempts = Column(Integer, default=0, nullable=False)
    locked_until = Column(TZDateTime, nullable=True)

    created_at = Column(TZDateTime, default=utc_now, nullable=False)
    updated_at = Column(TZDateTime, default=utc_now, onupdate=utc_now, nullable=False)

    def __repr__(self):
        return (
            f"<AdminUser(id={self.id}, username={self.username}, "
            f"role={self.role}, active={self.is_active})>"
        )

    def is_locked(self) -> bool:
        """Check if the user account is currently locked.

        Returns:
            True if account is locked, False otherwise.
        """
        if self.locked_until is None:
            return False
        return datetime.now(timezone.utc) < self.locked_until
