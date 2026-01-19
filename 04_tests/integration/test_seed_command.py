"""Integration tests for helix.py seed commands.

Tests the CLI seed commands for demo data seeding.
"""
import pytest
import subprocess
import sys
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from database.connection import Base
from database.models import PromptTemplate, PromptVersion


@pytest.fixture
def test_db_path(tmp_path):
    """Create a temporary database path for testing."""
    return tmp_path / "test_helix.db"


@pytest.fixture
def db_session(test_db_path):
    """Create a test database session."""
    engine = create_engine(
        f"sqlite:///{test_db_path}",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


class TestSeedCommand:
    """Tests for helix.py seed commands."""

    def test_seed_command_exists(self):
        """Test that seed command is recognized by helix.py."""
        result = subprocess.run(
            [sys.executable, "helix.py", "seed", "--help"],
            capture_output=True,
            text=True,
            timeout=10
        )

        # Should not show "Unknown command"
        assert "Unknown command" not in result.stdout
        assert "Unknown command" not in result.stderr

    def test_seed_demo_command_runs(self, test_db_path, monkeypatch):
        """Test that 'seed demo' command executes without error."""
        # Set DATABASE_URL to test database
        monkeypatch.setenv("DATABASE_URL", f"sqlite:///{test_db_path}")

        result = subprocess.run(
            [sys.executable, "helix.py", "seed", "demo"],
            capture_output=True,
            text=True,
            timeout=30,
            env={**subprocess.os.environ, "DATABASE_URL": f"sqlite:///{test_db_path}"}
        )

        # Command should complete successfully
        assert result.returncode == 0, f"Command failed: {result.stderr}"

    def test_seed_prompts_command_runs(self, test_db_path, monkeypatch):
        """Test that 'seed prompts' command executes without error."""
        monkeypatch.setenv("DATABASE_URL", f"sqlite:///{test_db_path}")

        result = subprocess.run(
            [sys.executable, "helix.py", "seed", "prompts"],
            capture_output=True,
            text=True,
            timeout=30,
            env={**subprocess.os.environ, "DATABASE_URL": f"sqlite:///{test_db_path}"}
        )

        assert result.returncode == 0, f"Command failed: {result.stderr}"

    def test_seed_reset_command_runs(self, test_db_path, monkeypatch):
        """Test that 'seed reset' command executes without error."""
        monkeypatch.setenv("DATABASE_URL", f"sqlite:///{test_db_path}")

        result = subprocess.run(
            [sys.executable, "helix.py", "seed", "reset"],
            capture_output=True,
            text=True,
            timeout=30,
            env={**subprocess.os.environ, "DATABASE_URL": f"sqlite:///{test_db_path}"}
        )

        assert result.returncode == 0, f"Command failed: {result.stderr}"

    def test_seed_demo_creates_prompts(self, test_db_path, db_session, monkeypatch):
        """Test that 'seed demo' actually creates prompt templates."""
        # First, run the seed demo command
        monkeypatch.setenv("DATABASE_URL", f"sqlite:///{test_db_path}")

        subprocess.run(
            [sys.executable, "helix.py", "seed", "demo"],
            capture_output=True,
            timeout=30,
            env={**subprocess.os.environ, "DATABASE_URL": f"sqlite:///{test_db_path}"}
        )

        # Check that demo prompts were created
        templates = db_session.query(PromptTemplate).filter(
            PromptTemplate.name.like("demo_%")
        ).all()

        assert len(templates) > 0, "No demo prompts were created"

    def test_seed_prompts_creates_default_prompts(self, test_db_path, db_session, monkeypatch):
        """Test that 'seed prompts' creates default prompt templates."""
        monkeypatch.setenv("DATABASE_URL", f"sqlite:///{test_db_path}")

        subprocess.run(
            [sys.executable, "helix.py", "seed", "prompts"],
            capture_output=True,
            timeout=30,
            env={**subprocess.os.environ, "DATABASE_URL": f"sqlite:///{test_db_path}"}
        )

        # Check that default prompts were created
        system_prompt = db_session.query(PromptTemplate).filter(
            PromptTemplate.name == "system_prompt"
        ).first()

        assert system_prompt is not None, "Default system prompt was not created"

    def test_seed_reset_clears_and_reseeds(self, test_db_path, db_session, monkeypatch):
        """Test that 'seed reset' clears existing data and re-seeds."""
        monkeypatch.setenv("DATABASE_URL", f"sqlite:///{test_db_path}")

        # First seed
        subprocess.run(
            [sys.executable, "helix.py", "seed", "demo"],
            capture_output=True,
            timeout=30,
            env={**subprocess.os.environ, "DATABASE_URL": f"sqlite:///{test_db_path}"}
        )

        initial_count = db_session.query(PromptTemplate).count()
        assert initial_count > 0

        # Reset and reseed
        subprocess.run(
            [sys.executable, "helix.py", "seed", "reset"],
            capture_output=True,
            timeout=30,
            env={**subprocess.os.environ, "DATABASE_URL": f"sqlite:///{test_db_path}"}
        )

        # Check that data was cleared and reseeded
        final_count = db_session.query(PromptTemplate).count()
        assert final_count > 0, "No data after reset"

    def test_seed_command_with_invalid_subcommand(self):
        """Test that invalid seed subcommand shows error."""
        result = subprocess.run(
            [sys.executable, "helix.py", "seed", "invalid"],
            capture_output=True,
            text=True,
            timeout=10
        )

        # Should fail with non-zero exit code
        assert result.returncode != 0
        # Should show error message (in stdout due to colored output)
        output = result.stdout.lower() + result.stderr.lower()
        assert "invalid" in output or "unknown" in output
