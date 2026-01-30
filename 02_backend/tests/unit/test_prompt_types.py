"""
Unit tests for PromptType enum.

Tests that prompt types are properly defined and constrained to valid values.
"""
import pytest
from enum import Enum


class TestPromptTypeEnum:
    """Test suite for PromptType enumeration."""

    def test_prompt_type_is_enum(self):
        """Test that PromptType is an enum class."""
        from core.constants import PromptType

        assert issubclass(PromptType, Enum)

    def test_prompt_type_has_system_prompt(self):
        """Test that SYSTEM_PROMPT type exists."""
        from core.constants import PromptType

        assert PromptType.SYSTEM_PROMPT.value == "system_prompt"

    def test_prompt_type_has_greeting(self):
        """Test that GREETING type exists."""
        from core.constants import PromptType

        assert PromptType.GREETING.value == "greeting"

    def test_prompt_type_has_farewell(self):
        """Test that FAREWELL type exists."""
        from core.constants import PromptType

        assert PromptType.FAREWELL.value == "farewell"

    def test_prompt_type_has_rejection(self):
        """Test that REJECTION type exists."""
        from core.constants import PromptType

        assert PromptType.REJECTION.value == "rejection"

    def test_prompt_type_has_clarification(self):
        """Test that CLARIFICATION type exists."""
        from core.constants import PromptType

        assert PromptType.CLARIFICATION.value == "clarification"

    def test_prompt_type_has_handoff(self):
        """Test that HANDOFF type exists."""
        from core.constants import PromptType

        assert PromptType.HANDOFF.value == "handoff"

    def test_prompt_type_has_retrieval(self):
        """Test that RETRIEVAL type exists."""
        from core.constants import PromptType

        assert PromptType.RETRIEVAL.value == "retrieval"

    def test_prompt_type_has_fallback(self):
        """Test that FALLBACK type exists."""
        from core.constants import PromptType

        assert PromptType.FALLBACK.value == "fallback"

    def test_prompt_type_is_valid_returns_true_for_valid_types(self):
        """Test that is_valid_type returns True for valid types."""
        from core.constants import PromptType

        assert PromptType.is_valid_type("system_prompt") is True
        assert PromptType.is_valid_type("greeting") is True
        assert PromptType.is_valid_type("retrieval") is True

    def test_prompt_type_is_valid_returns_false_for_invalid_types(self):
        """Test that is_valid_type returns False for invalid types."""
        from core.constants import PromptType

        assert PromptType.is_valid_type("invalid_type") is False
        assert PromptType.is_valid_type("random") is False
        assert PromptType.is_valid_type("") is False

    def test_prompt_type_get_all_types_returns_list(self):
        """Test that get_all_types returns list of all valid types."""
        from core.constants import PromptType

        all_types = PromptType.get_all_types()

        assert isinstance(all_types, list)
        assert len(all_types) == 8
        assert "system_prompt" in all_types
        assert "greeting" in all_types
        assert "retrieval" in all_types
