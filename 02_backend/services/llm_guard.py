"""
LLM Guard Service for token limit enforcement.

Provides:
- Token counting (approximate)
- Input/output token limits
- Conversation token tracking
- Truncation with warnings
- Abuse pattern detection

Default limits:
- MAX_INPUT_TOKENS: 2000
- MAX_OUTPUT_TOKENS: 1000
- MAX_CONVERSATION_TOKENS: 8000
"""
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime

# Default token limits
DEFAULT_MAX_INPUT_TOKENS = 2000
DEFAULT_MAX_OUTPUT_TOKENS = 1000
DEFAULT_MAX_CONVERSATION_TOKENS = 8000


@dataclass
class TokenLimitConfig:
    """Configuration for token limits."""
    max_input_tokens: int = DEFAULT_MAX_INPUT_TOKENS
    max_output_tokens: int = DEFAULT_MAX_OUTPUT_TOKENS
    max_conversation_tokens: int = DEFAULT_MAX_CONVERSATION_TOKENS


@dataclass
class TruncationResult:
    """Result of text truncation."""
    text: str
    was_truncated: bool
    original_tokens: int = 0
    final_tokens: int = 0


@dataclass
class TokenLimitResult:
    """Result of token limit check."""
    allowed: bool
    was_truncated: bool = False
    truncated_text: str = ""
    warning: Optional[str] = None
    original_tokens: int = 0


@dataclass
class ConversationStats:
    """Statistics for conversation token usage."""
    total_tokens: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    turn_count: int = 0


def count_tokens(text: str) -> int:
    """
    Count approximate tokens in text.

    Uses a simple heuristic: ~4 characters per token for English.
    For production, use tiktoken or the model's tokenizer.

    Args:
        text: Text to count

    Returns:
        int: Approximate token count
    """
    if not text:
        return 0

    # Simple approximation: split on whitespace and punctuation
    # Average English word is ~5 chars, ~1.3 tokens
    # So roughly 4 chars per token
    char_count = len(text)
    return max(1, char_count // 4)


def truncate_to_token_limit(
    text: str,
    max_tokens: int
) -> TruncationResult:
    """
    Truncate text to fit within token limit.

    Tries to truncate at word boundaries and adds indicator.

    Args:
        text: Text to truncate
        max_tokens: Maximum tokens allowed

    Returns:
        TruncationResult: Truncated text with metadata
    """
    if not text:
        return TruncationResult(
            text="",
            was_truncated=False,
            original_tokens=0,
            final_tokens=0
        )

    original_tokens = count_tokens(text)

    if original_tokens <= max_tokens:
        return TruncationResult(
            text=text,
            was_truncated=False,
            original_tokens=original_tokens,
            final_tokens=original_tokens
        )

    # Estimate character limit (4 chars per token)
    # Leave room for truncation indicator
    char_limit = (max_tokens - 5) * 4

    if char_limit < 10:
        char_limit = 10

    truncated = text[:char_limit]

    # Try to truncate at word boundary
    last_space = truncated.rfind(" ")
    if last_space > char_limit // 2:
        truncated = truncated[:last_space]

    truncated = truncated.rstrip() + "... [truncated]"

    final_tokens = count_tokens(truncated)

    return TruncationResult(
        text=truncated,
        was_truncated=True,
        original_tokens=original_tokens,
        final_tokens=final_tokens
    )


def check_token_limits(
    text: str,
    config: TokenLimitConfig
) -> TokenLimitResult:
    """
    Check if text is within token limits.

    Args:
        text: Text to check
        config: Token limit configuration

    Returns:
        TokenLimitResult: Check result with truncated text if needed
    """
    token_count = count_tokens(text)

    if token_count <= config.max_input_tokens:
        return TokenLimitResult(
            allowed=True,
            truncated_text=text,
            original_tokens=token_count
        )

    # Truncate to limit
    result = truncate_to_token_limit(text, config.max_input_tokens)

    return TokenLimitResult(
        allowed=True,
        was_truncated=True,
        truncated_text=result.text,
        warning=f"Input was truncated from {result.original_tokens} to {result.final_tokens} tokens",
        original_tokens=result.original_tokens
    )


class LLMGuard:
    """
    Guards LLM interactions with token limits and abuse detection.

    Features:
    - Input/output token limit enforcement
    - Conversation token tracking
    - Abuse pattern detection
    - Request counting
    """

    def __init__(self, config: Optional[TokenLimitConfig] = None):
        """
        Initialize LLM guard.

        Args:
            config: Token limit configuration
        """
        self.config = config or TokenLimitConfig()
        self._conversation_tokens: int = 0
        self._request_count: int = 0
        self._abuse_count: int = 0
        self._truncation_count: int = 0
        self._start_time: datetime = datetime.utcnow()

    @property
    def request_count(self) -> int:
        """Get total request count."""
        return self._request_count

    @property
    def abuse_count(self) -> int:
        """Get abuse detection count."""
        return self._abuse_count

    def check_input(self, text: str) -> TokenLimitResult:
        """
        Check input against token limits.

        Args:
            text: Input text to check

        Returns:
            TokenLimitResult: Check result
        """
        self._request_count += 1

        result = check_token_limits(text, self.config)

        if result.was_truncated:
            self._truncation_count += 1
            # Log abuse if too many truncations
            if self._truncation_count >= 5:
                self._abuse_count += 1

        return result

    def check_output(self, text: str) -> TokenLimitResult:
        """
        Check output against token limits.

        Args:
            text: Output text to check

        Returns:
            TokenLimitResult: Check result
        """
        token_count = count_tokens(text)

        if token_count <= self.config.max_output_tokens:
            return TokenLimitResult(
                allowed=True,
                truncated_text=text,
                original_tokens=token_count
            )

        # Truncate output
        result = truncate_to_token_limit(text, self.config.max_output_tokens)

        return TokenLimitResult(
            allowed=True,
            was_truncated=True,
            truncated_text=result.text,
            warning=f"Output was truncated from {result.original_tokens} to {result.final_tokens} tokens",
            original_tokens=result.original_tokens
        )

    def add_to_conversation(self, text: str, tokens: Optional[int] = None) -> None:
        """
        Add tokens to conversation total.

        Args:
            text: Text to add (used for counting if tokens not provided)
            tokens: Pre-counted token count
        """
        if tokens is not None:
            self._conversation_tokens += tokens
        else:
            self._conversation_tokens += count_tokens(text)

    def get_conversation_stats(self) -> ConversationStats:
        """
        Get conversation statistics.

        Returns:
            ConversationStats: Current stats
        """
        return ConversationStats(
            total_tokens=self._conversation_tokens,
            turn_count=self._request_count
        )

    def is_conversation_over_limit(self) -> bool:
        """
        Check if conversation has exceeded token limit.

        Returns:
            bool: True if over limit
        """
        return self._conversation_tokens >= self.config.max_conversation_tokens

    def reset_conversation(self) -> None:
        """Reset conversation token count."""
        self._conversation_tokens = 0
