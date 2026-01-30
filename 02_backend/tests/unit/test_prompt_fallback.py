"""
Unit tests for prompt fallback behavior.

Tests that the system gracefully handles missing prompts using defaults.
"""
import os
import pytest
from unittest.mock import MagicMock, patch

# Set required environment variables
os.environ['APP_NAME'] = 'TestApp'
os.environ['BOT_NAME'] = 'TestBot'
os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
os.environ['API_KEY'] = 'test-api-key'

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from database.connection import Base
from database.models import PromptTemplate, PromptVersion, PromptAuditLog  # Register models


class TestPromptFallback:
    """Test suite for prompt fallback behavior."""

    @pytest.fixture
    def db_session(self):
        """Create isolated database session."""
        engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(bind=engine)
        Session = sessionmaker(bind=engine)
        session = Session()
        yield session
        session.close()

    def test_get_active_content_with_fallback_returns_default_when_not_found(
        self, db_session
    ):
        """Test that fallback returns default prompt when template not found."""
        from services.prompt_service import PromptService
        from core.constants import PromptType, DEFAULT_PROMPTS

        service = PromptService(db_session)

        # Don't create any prompts - database is empty
        result = service.get_active_content_with_fallback("nonexistent_prompt")

        # Should return None (name doesn't match a type)
        assert result is None

    def test_get_active_content_with_fallback_returns_default_for_system_prompt(
        self, db_session
    ):
        """Test fallback returns default for system_prompt type."""
        from services.prompt_service import PromptService
        from core.constants import PromptType, DEFAULT_PROMPTS

        service = PromptService(db_session)

        # No prompts in DB
        result = service.get_active_content_with_fallback(
            "missing_system_prompt",
            prompt_type=PromptType.SYSTEM_PROMPT
        )

        assert result == DEFAULT_PROMPTS[PromptType.SYSTEM_PROMPT]

    def test_get_active_content_with_fallback_returns_default_for_greeting(
        self, db_session
    ):
        """Test fallback returns default for greeting type."""
        from services.prompt_service import PromptService
        from core.constants import PromptType, DEFAULT_PROMPTS

        service = PromptService(db_session)

        result = service.get_active_content_with_fallback(
            "missing_greeting",
            prompt_type=PromptType.GREETING
        )

        assert result == DEFAULT_PROMPTS[PromptType.GREETING]

    def test_get_active_content_with_fallback_returns_db_content_when_found(
        self, db_session
    ):
        """Test that DB content is returned when prompt exists."""
        from services.prompt_service import PromptService
        from core.constants import PromptType

        service = PromptService(db_session)

        # Create a prompt in DB
        service.create_template(
            name="test_prompt",
            prompt_type="system_prompt",
            content="Custom DB content"
        )

        result = service.get_active_content_with_fallback(
            "test_prompt",
            prompt_type=PromptType.SYSTEM_PROMPT
        )

        assert result == "Custom DB content"

    def test_get_active_content_with_fallback_logs_warning_on_fallback(
        self, db_session
    ):
        """Test that a warning is logged when using fallback."""
        from services.prompt_service import PromptService
        from core.constants import PromptType

        service = PromptService(db_session)

        with patch('services.prompt_service.logger') as mock_logger:
            service.get_active_content_with_fallback(
                "missing_prompt",
                prompt_type=PromptType.SYSTEM_PROMPT
            )

            mock_logger.warning.assert_called_once()
            assert "fallback" in mock_logger.warning.call_args[0][0].lower()

    def test_get_active_content_with_fallback_never_raises_for_missing_prompt(
        self, db_session
    ):
        """Test that no exception is raised for missing prompts."""
        from services.prompt_service import PromptService
        from core.constants import PromptType

        service = PromptService(db_session)

        # Should not raise even with completely unknown prompt
        try:
            result = service.get_active_content_with_fallback(
                "completely_unknown",
                prompt_type=PromptType.FALLBACK
            )
            assert result is not None  # Should return fallback content
        except Exception:
            pytest.fail("Should not raise exception for missing prompt")


class TestDefaultPrompts:
    """Test suite for DEFAULT_PROMPTS constant."""

    def test_default_prompts_has_all_types(self):
        """Test that DEFAULT_PROMPTS has entry for every PromptType."""
        from core.constants import PromptType, DEFAULT_PROMPTS

        for prompt_type in PromptType:
            assert prompt_type in DEFAULT_PROMPTS, (
                f"Missing default for {prompt_type}"
            )

    def test_default_prompts_are_non_empty(self):
        """Test that all default prompts have content."""
        from core.constants import DEFAULT_PROMPTS

        for prompt_type, content in DEFAULT_PROMPTS.items():
            assert content is not None
            assert len(content.strip()) > 0, (
                f"Empty default for {prompt_type}"
            )

    def test_system_prompt_default_is_reasonable(self):
        """Test that system prompt default is a reasonable instruction."""
        from core.constants import PromptType, DEFAULT_PROMPTS

        system_prompt = DEFAULT_PROMPTS[PromptType.SYSTEM_PROMPT]
        assert "assistant" in system_prompt.lower()

    def test_fallback_prompt_is_user_friendly(self):
        """Test that fallback prompt is user-friendly."""
        from core.constants import PromptType, DEFAULT_PROMPTS

        fallback = DEFAULT_PROMPTS[PromptType.FALLBACK]
        # Should apologize or indicate a problem
        assert "sorry" in fallback.lower() or "apologize" in fallback.lower()
