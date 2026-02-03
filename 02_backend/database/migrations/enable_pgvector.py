"""Enable pgvector extension migration.

This migration enables the pgvector extension for PostgreSQL databases.
It gracefully skips on non-PostgreSQL databases (e.g., SQLite).

Revision: 001
Create Date: 2024-01-01
"""
import logging
from dataclasses import dataclass
from typing import Optional

from sqlalchemy import text
from sqlalchemy.engine import Engine


logger = logging.getLogger(__name__)


@dataclass
class MigrationResult:
    """Result of a migration operation.

    Attributes:
        success: Whether the migration completed without errors.
        skipped: Whether the migration was skipped (e.g., wrong database type).
        message: Human-readable message about the result.
        pgvector_version: Version of pgvector if detected.
        warning: Optional warning message (e.g., data loss warning).
    """

    success: bool
    skipped: bool
    message: str
    pgvector_version: Optional[str] = None
    warning: Optional[str] = None


def upgrade(engine: Engine) -> MigrationResult:
    """Apply pgvector extension migration.

    Creates the pgvector extension if it doesn't exist.
    Uses IF NOT EXISTS for idempotency.

    Args:
        engine: SQLAlchemy engine instance.

    Returns:
        MigrationResult with operation details.
    """
    if engine.dialect.name != "postgresql":
        logger.info("Skipping pgvector migration: database is not PostgreSQL")
        return MigrationResult(
            success=True,
            skipped=True,
            message="Migration skipped: database is not PostgreSQL (SQLite or other)",
            pgvector_version=None
        )

    try:
        with engine.connect() as conn:
            # Create extension if not exists (idempotent)
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            conn.commit()

            # Get pgvector version
            result = conn.execute(
                text("SELECT extversion FROM pg_extension WHERE extname = 'vector'")
            )
            version_row = result.scalar()
            pgvector_version = version_row if version_row else None

            if pgvector_version:
                logger.info(f"pgvector extension enabled, version: {pgvector_version}")
            else:
                logger.info("pgvector extension enabled")

            return MigrationResult(
                success=True,
                skipped=False,
                message="pgvector extension enabled successfully",
                pgvector_version=pgvector_version
            )

    except Exception as e:
        logger.error(f"Failed to enable pgvector extension: {e}")
        return MigrationResult(
            success=False,
            skipped=False,
            message=f"Migration failed: {str(e)}",
            pgvector_version=None
        )


def downgrade(engine: Engine) -> MigrationResult:
    """Remove pgvector extension.

    Warns if embeddings exist before dropping the extension.

    Args:
        engine: SQLAlchemy engine instance.

    Returns:
        MigrationResult with operation details.
    """
    if engine.dialect.name != "postgresql":
        logger.info("Skipping pgvector downgrade: database is not PostgreSQL")
        return MigrationResult(
            success=True,
            skipped=True,
            message="Downgrade skipped: database is not PostgreSQL",
            pgvector_version=None
        )

    warning = None

    try:
        with engine.connect() as conn:
            # Check for existing embeddings
            # Try to count rows in any table with vector columns
            try:
                result = conn.execute(
                    text("""
                        SELECT COUNT(*) FROM information_schema.columns
                        WHERE udt_name = 'vector'
                    """)
                )
                vector_column_count = result.scalar() or 0

                if vector_column_count > 0:
                    warning = f"WARNING: {vector_column_count} vector columns exist. Dropping extension will cause data loss."
                    logger.warning(warning)
            except Exception:
                # Table might not exist, that's okay
                pass

            # Drop extension
            conn.execute(text("DROP EXTENSION IF EXISTS vector CASCADE"))
            conn.commit()

            logger.info("pgvector extension dropped")

            return MigrationResult(
                success=True,
                skipped=False,
                message="pgvector extension dropped",
                pgvector_version=None,
                warning=warning
            )

    except Exception as e:
        logger.error(f"Failed to drop pgvector extension: {e}")
        return MigrationResult(
            success=False,
            skipped=False,
            message=f"Downgrade failed: {str(e)}",
            pgvector_version=None
        )


def check_status(engine: Engine) -> MigrationResult:
    """Check current pgvector status.

    Args:
        engine: SQLAlchemy engine instance.

    Returns:
        MigrationResult with current status.
    """
    if engine.dialect.name != "postgresql":
        return MigrationResult(
            success=True,
            skipped=True,
            message="Not PostgreSQL - pgvector not applicable",
            pgvector_version=None
        )

    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT extversion FROM pg_extension WHERE extname = 'vector'")
            )
            version = result.scalar()

            if version:
                return MigrationResult(
                    success=True,
                    skipped=False,
                    message=f"pgvector is enabled",
                    pgvector_version=version
                )
            else:
                return MigrationResult(
                    success=True,
                    skipped=False,
                    message="pgvector is not enabled",
                    pgvector_version=None
                )

    except Exception as e:
        return MigrationResult(
            success=False,
            skipped=False,
            message=f"Status check failed: {str(e)}",
            pgvector_version=None
        )
