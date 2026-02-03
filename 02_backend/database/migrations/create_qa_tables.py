"""Create QAPair and Embedding tables migration.

This migration creates the knowledge base tables:
- qa_pair: Stores question-answer pairs
- embedding: Stores vector embeddings for semantic search

Includes HNSW index for PostgreSQL with pgvector.

Revision: 002
Create Date: 2026-02-03
Dependencies: 001 (pgvector extension must be enabled first)
"""
import logging
from dataclasses import dataclass
from typing import Optional

from sqlalchemy import text
from sqlalchemy.engine import Engine

from models.base import BaseModel


logger = logging.getLogger(__name__)


@dataclass
class MigrationResult:
    """Result of a migration operation.

    Attributes:
        success: Whether the migration completed without errors.
        skipped: Whether the migration was skipped (e.g., tables exist).
        message: Human-readable message about the result.
        tables_created: List of tables created.
        indexes_created: List of indexes created.
        warning: Optional warning message.
    """

    success: bool
    skipped: bool
    message: str
    tables_created: list = None
    indexes_created: list = None
    warning: Optional[str] = None

    def __post_init__(self):
        if self.tables_created is None:
            self.tables_created = []
        if self.indexes_created is None:
            self.indexes_created = []


def upgrade(engine: Engine) -> MigrationResult:
    """Apply QA tables migration.

    Creates qa_pair and embedding tables with appropriate indexes.
    On PostgreSQL with pgvector, adds HNSW index for vector similarity search.

    Args:
        engine: SQLAlchemy engine instance.

    Returns:
        MigrationResult with operation details.
    """
    tables_created = []
    indexes_created = []

    try:
        # Create tables using SQLAlchemy metadata
        # This handles both SQLite (JSON vector) and PostgreSQL (native types)
        BaseModel.metadata.create_all(bind=engine, checkfirst=True)
        tables_created = ["qa_pair", "embedding"]

        logger.info(f"Created tables: {tables_created}")

        # Add HNSW index for PostgreSQL with pgvector
        if engine.dialect.name == "postgresql":
            try:
                with engine.connect() as conn:
                    # Check if pgvector is available
                    result = conn.execute(
                        text("SELECT extname FROM pg_extension WHERE extname = 'vector'")
                    )
                    if result.fetchone() is not None:
                        # Alter vector column to use Vector type if needed
                        # (Our model uses JSON by default for SQLite compatibility)
                        conn.execute(text("""
                            DO $$
                            BEGIN
                                -- Try to alter the column to Vector type
                                -- This will fail silently if already correct type
                                BEGIN
                                    ALTER TABLE embedding
                                    ALTER COLUMN vector TYPE vector(1536)
                                    USING vector::vector(1536);
                                EXCEPTION
                                    WHEN others THEN
                                        -- Column might already be correct type, ignore
                                        NULL;
                                END;
                            END $$;
                        """))

                        # Create HNSW index for cosine similarity
                        conn.execute(text("""
                            CREATE INDEX IF NOT EXISTS ix_embedding_vector_hnsw
                            ON embedding
                            USING hnsw (vector vector_cosine_ops)
                            WITH (m = 16, ef_construction = 64)
                        """))
                        conn.commit()

                        indexes_created.append("ix_embedding_vector_hnsw (HNSW)")
                        logger.info("Created HNSW index on embedding.vector")
                    else:
                        logger.warning("pgvector not available, skipping HNSW index")

            except Exception as e:
                logger.warning(f"Could not create HNSW index: {e}")
                # Non-fatal - tables are still created

        return MigrationResult(
            success=True,
            skipped=False,
            message="QA tables created successfully",
            tables_created=tables_created,
            indexes_created=indexes_created
        )

    except Exception as e:
        logger.error(f"Failed to create QA tables: {e}")
        return MigrationResult(
            success=False,
            skipped=False,
            message=f"Migration failed: {str(e)}",
            tables_created=tables_created,
            indexes_created=indexes_created
        )


def downgrade(engine: Engine) -> MigrationResult:
    """Remove QA tables.

    Drops embedding table first (foreign key constraint), then qa_pair.

    Args:
        engine: SQLAlchemy engine instance.

    Returns:
        MigrationResult with operation details.
    """
    warning = None
    tables_dropped = []

    try:
        with engine.connect() as conn:
            # Check for existing data
            try:
                result = conn.execute(text("SELECT COUNT(*) FROM qa_pair"))
                qa_count = result.scalar() or 0
                if qa_count > 0:
                    warning = f"WARNING: {qa_count} QA pairs will be deleted"
                    logger.warning(warning)
            except Exception:
                pass  # Table might not exist

            # Drop tables in correct order (embedding first due to FK)
            try:
                conn.execute(text("DROP TABLE IF EXISTS embedding CASCADE"))
                tables_dropped.append("embedding")
            except Exception as e:
                logger.warning(f"Could not drop embedding table: {e}")

            try:
                conn.execute(text("DROP TABLE IF EXISTS qa_pair CASCADE"))
                tables_dropped.append("qa_pair")
            except Exception as e:
                logger.warning(f"Could not drop qa_pair table: {e}")

            conn.commit()

        logger.info(f"Dropped tables: {tables_dropped}")

        return MigrationResult(
            success=True,
            skipped=False,
            message="QA tables dropped",
            tables_created=[],
            indexes_created=[],
            warning=warning
        )

    except Exception as e:
        logger.error(f"Failed to drop QA tables: {e}")
        return MigrationResult(
            success=False,
            skipped=False,
            message=f"Downgrade failed: {str(e)}",
            warning=warning
        )


def check_status(engine: Engine) -> MigrationResult:
    """Check QA tables status.

    Args:
        engine: SQLAlchemy engine instance.

    Returns:
        MigrationResult with current status.
    """
    tables_found = []
    indexes_found = []

    try:
        with engine.connect() as conn:
            # Check for tables
            if engine.dialect.name == "postgresql":
                result = conn.execute(text("""
                    SELECT table_name FROM information_schema.tables
                    WHERE table_name IN ('qa_pair', 'embedding')
                    AND table_schema = 'public'
                """))
            else:
                result = conn.execute(text("""
                    SELECT name FROM sqlite_master
                    WHERE type='table' AND name IN ('qa_pair', 'embedding')
                """))

            for row in result:
                tables_found.append(row[0])

            # Check for HNSW index (PostgreSQL only)
            if engine.dialect.name == "postgresql":
                try:
                    result = conn.execute(text("""
                        SELECT indexname FROM pg_indexes
                        WHERE tablename = 'embedding'
                        AND indexname LIKE '%hnsw%'
                    """))
                    for row in result:
                        indexes_found.append(row[0])
                except Exception:
                    pass

        if tables_found:
            return MigrationResult(
                success=True,
                skipped=False,
                message=f"Tables exist: {tables_found}",
                tables_created=tables_found,
                indexes_created=indexes_found
            )
        else:
            return MigrationResult(
                success=True,
                skipped=False,
                message="QA tables do not exist",
                tables_created=[],
                indexes_created=[]
            )

    except Exception as e:
        return MigrationResult(
            success=False,
            skipped=False,
            message=f"Status check failed: {str(e)}"
        )
