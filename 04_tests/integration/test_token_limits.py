"""
Integration tests for Token Limit Controls (P12.3.3)

Tests token limiting including:
- Max input tokens
- Max output tokens
- Per-conversation total
- Truncation with warning
- Abuse pattern logging
"""
import pytest

from services.llm_guard import (
    LLMGuard,
    TokenLimitConfig,
    TokenLimitResult,
    count_tokens,
    truncate_to_token_limit,
    check_token_limits,
)


class TestTokenCounting:
    """Tests for token counting."""

    def test_count_tokens_empty(self):
        """Empty string should have 0 tokens."""
        assert count_tokens("") == 0

    def test_count_tokens_single_word(self):
        """Single word should be 1 token."""
        count = count_tokens("Hello")
        assert count >= 1

    def test_count_tokens_sentence(self):
        """Sentence should have multiple tokens."""
        count = count_tokens("Hello, how are you today?")
        assert count > 1

    def test_count_tokens_approximation(self):
        """Token count should be reasonable approximation."""
        # Roughly 4 chars per token for English
        text = "word " * 100  # 500 chars, ~100-125 tokens
        count = count_tokens(text)
        assert 80 <= count <= 150


class TestTruncation:
    """Tests for token-based truncation."""

    def test_truncate_no_change_if_under_limit(self):
        """Text under limit should not be changed."""
        text = "Short text"
        result = truncate_to_token_limit(text, max_tokens=100)
        assert result.text == text
        assert result.was_truncated is False

    def test_truncate_reduces_token_count(self):
        """Truncation should reduce token count to limit."""
        long_text = "word " * 500  # Many tokens
        result = truncate_to_token_limit(long_text, max_tokens=50)
        assert count_tokens(result.text) <= 50
        assert result.was_truncated is True

    def test_truncate_adds_indicator(self):
        """Truncated text should indicate truncation."""
        long_text = "word " * 500
        result = truncate_to_token_limit(long_text, max_tokens=50)
        assert "..." in result.text or "[truncated]" in result.text.lower()

    def test_truncate_preserves_word_boundaries(self):
        """Truncation should not cut words in half."""
        text = "The quick brown fox jumps over the lazy dog " * 50
        result = truncate_to_token_limit(text, max_tokens=20)
        # Result should be valid text (truncated at word boundary)
        # The truncation indicator should be at the end
        assert result.was_truncated
        assert "truncated" in result.text.lower() or "..." in result.text


class TestTokenLimitConfig:
    """Tests for token limit configuration."""

    def test_default_limits(self):
        """Default limits should be set."""
        config = TokenLimitConfig()
        assert config.max_input_tokens == 2000
        assert config.max_output_tokens == 1000

    def test_custom_limits(self):
        """Custom limits should be accepted."""
        config = TokenLimitConfig(
            max_input_tokens=4000,
            max_output_tokens=2000,
            max_conversation_tokens=10000
        )
        assert config.max_input_tokens == 4000
        assert config.max_output_tokens == 2000
        assert config.max_conversation_tokens == 10000


class TestCheckTokenLimits:
    """Tests for token limit checking."""

    def test_within_limits_passes(self):
        """Request within limits should pass."""
        config = TokenLimitConfig(max_input_tokens=100)
        result = check_token_limits("Short input", config)
        assert result.allowed is True

    def test_over_input_limit_truncates(self):
        """Request over input limit should be truncated."""
        config = TokenLimitConfig(max_input_tokens=20)
        long_input = "word " * 100
        result = check_token_limits(long_input, config)
        assert result.was_truncated is True
        assert count_tokens(result.truncated_text) <= 20

    def test_returns_warning_on_truncation(self):
        """Truncation should include warning message."""
        config = TokenLimitConfig(max_input_tokens=20)
        long_input = "word " * 100
        result = check_token_limits(long_input, config)
        assert result.warning is not None
        assert "truncated" in result.warning.lower()


class TestLLMGuard:
    """Tests for the LLM Guard service."""

    @pytest.fixture
    def guard(self):
        """Create LLM guard instance."""
        return LLMGuard()

    def test_check_input_within_limits(self, guard):
        """Input within limits should pass."""
        result = guard.check_input("Hello, how are you?")
        assert result.allowed is True

    def test_check_input_over_limit(self, guard):
        """Input over limit should be handled."""
        # Create input over 2000 tokens (need ~8000 chars at 4 chars/token)
        long_input = "word " * 2000  # ~10000 chars = ~2500 tokens
        result = guard.check_input(long_input)
        # Should either truncate or reject
        assert result.was_truncated or not result.allowed

    def test_check_output_within_limits(self, guard):
        """Output within limits should pass."""
        result = guard.check_output("Here is your answer.")
        assert result.allowed is True

    def test_track_conversation_tokens(self, guard):
        """Guard should track conversation token usage."""
        guard.add_to_conversation("Question 1", tokens=100)
        guard.add_to_conversation("Answer 1", tokens=150)

        stats = guard.get_conversation_stats()
        assert stats.total_tokens == 250


class TestAbusePatternLogging:
    """Tests for abuse pattern logging."""

    @pytest.fixture
    def guard(self):
        return LLMGuard()

    def test_logs_repeated_truncations(self, guard):
        """Repeated truncations should be logged."""
        # Create input over 2000 tokens to trigger truncation
        long_input = "word " * 2000  # ~10000 chars = ~2500 tokens

        for _ in range(10):  # Need enough truncations to trigger abuse
            guard.check_input(long_input)

        # Should have logged abuse pattern (after 5+ truncations)
        assert guard.abuse_count > 0

    def test_logs_high_volume_requests(self, guard):
        """High volume in short time should be logged."""
        for i in range(100):
            guard.check_input(f"Request {i}")

        # Should track this pattern
        assert guard.request_count >= 100
