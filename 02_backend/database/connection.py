"""Database connection management for Helix."""
import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import StaticPool


def get_database_url() -> str:
    """Get database URL from environment.

    Returns:
        Database URL string. Defaults to SQLite in-memory for tests.
    """
    db_url = os.getenv("DATABASE_URL") or os.getenv("DB_DSN")

    if db_url:
        # Convert asyncpg to psycopg2 if needed
        if "postgresql+asyncpg://" in db_url:
            return db_url.replace("postgresql+asyncpg://", "postgresql+psycopg2://")
        return db_url

    # Default to SQLite in-memory for tests
    return "sqlite:///:memory:"


DATABASE_URL = get_database_url()


def create_db_engine(url: str | None = None):
    """Create database engine with appropriate settings.

    Args:
        url: Optional database URL. Uses DATABASE_URL if not provided.

    Returns:
        SQLAlchemy engine instance.
    """
    db_url = url or DATABASE_URL

    if db_url.startswith("sqlite"):
        if ":memory:" in db_url:
            return create_engine(
                "sqlite:///:memory:?cache=shared",
                connect_args={"check_same_thread": False},
                poolclass=StaticPool,
            )
        return create_engine(
            db_url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )

    if db_url.startswith("postgresql"):
        return create_engine(db_url, pool_pre_ping=True)

    # Default to SQLite
    return create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )


# Create engine and session factory
engine = create_db_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


def get_db():
    """Get database session.

    Yields:
        Database session instance.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database by creating all tables."""
    Base.metadata.create_all(bind=engine)
