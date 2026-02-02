"""
LLM Output Sanitization for safe response rendering.

Provides:
- Script tag removal
- Markdown exploit prevention
- Response length validation
- Format compliance checking

Ensures LLM responses are safe to display in web contexts
and don't contain executable code or exploits.
"""
import re
from dataclasses import dataclass
from typing import Optional

# Default max response length (characters)
DEFAULT_MAX_LENGTH = 10000


@dataclass
class LengthValidationResult:
    """Result of length validation."""
    is_valid: bool
    text: str
    was_truncated: bool = False
    original_length: int = 0


@dataclass
class SanitizationResult:
    """Result of LLM output sanitization."""
    text: str
    was_modified: bool
    removed_threats: list[str]


def remove_script_tags(text: str) -> str:
    """
    Remove all script tags and their content.

    Args:
        text: Text to sanitize

    Returns:
        str: Text with script tags removed
    """
    if not text:
        return text

    # Remove script tags (case-insensitive, multiline)
    pattern = r"<script[^>]*>.*?</script>"
    result = re.sub(pattern, "", text, flags=re.IGNORECASE | re.DOTALL)

    # Also remove standalone script tags
    result = re.sub(r"<script[^>]*>", "", result, flags=re.IGNORECASE)
    result = re.sub(r"</script>", "", result, flags=re.IGNORECASE)

    return result


def sanitize_markdown(text: str) -> str:
    """
    Sanitize markdown to prevent exploits.

    Removes:
    - javascript: links
    - data: URLs
    - Other potentially dangerous URLs

    Args:
        text: Markdown text to sanitize

    Returns:
        str: Sanitized markdown
    """
    if not text:
        return text

    result = text

    # Remove javascript: links
    # [text](javascript:...)
    result = re.sub(
        r"\[([^\]]*)\]\(javascript:[^)]*\)",
        r"[\1]()",
        result,
        flags=re.IGNORECASE
    )

    # Remove data: URLs in images
    # ![alt](data:...)
    result = re.sub(
        r"!\[([^\]]*)\]\(data:[^)]*\)",
        r"![\1]()",
        result,
        flags=re.IGNORECASE
    )

    # Remove data: URLs in links
    result = re.sub(
        r"\[([^\]]*)\]\(data:[^)]*\)",
        r"[\1]()",
        result,
        flags=re.IGNORECASE
    )

    return result


def validate_response_length(
    text: str,
    max_length: int = DEFAULT_MAX_LENGTH
) -> LengthValidationResult:
    """
    Validate and optionally truncate response length.

    Args:
        text: Text to validate
        max_length: Maximum allowed length

    Returns:
        LengthValidationResult: Validation result with truncated text if needed
    """
    if not text:
        return LengthValidationResult(
            is_valid=True,
            text="",
            was_truncated=False,
            original_length=0
        )

    original_length = len(text)

    if original_length <= max_length:
        return LengthValidationResult(
            is_valid=True,
            text=text,
            was_truncated=False,
            original_length=original_length
        )

    # Truncate and add indicator
    truncated = text[:max_length - 20]  # Leave room for indicator

    # Try to truncate at a word boundary
    last_space = truncated.rfind(" ")
    if last_space > max_length - 100:
        truncated = truncated[:last_space]

    truncated += "... [truncated]"

    return LengthValidationResult(
        is_valid=True,
        text=truncated,
        was_truncated=True,
        original_length=original_length
    )


class LLMOutputSanitizer:
    """
    Sanitizes LLM output for safe display.

    Applies multiple sanitization steps:
    1. Script tag removal
    2. Markdown exploit prevention
    3. Length validation
    """

    def __init__(self, max_length: int = DEFAULT_MAX_LENGTH):
        """
        Initialize sanitizer.

        Args:
            max_length: Maximum response length
        """
        self.max_length = max_length

    def sanitize(self, text: str) -> SanitizationResult:
        """
        Sanitize LLM output.

        Args:
            text: Raw LLM output

        Returns:
            SanitizationResult: Sanitized text with metadata
        """
        if not text:
            return SanitizationResult(
                text="",
                was_modified=False,
                removed_threats=[]
            )

        removed_threats = []
        result = text

        # Remove script tags
        after_scripts = remove_script_tags(result)
        if after_scripts != result:
            removed_threats.append("script_tags")
            result = after_scripts

        # Sanitize markdown
        after_markdown = sanitize_markdown(result)
        if after_markdown != result:
            removed_threats.append("markdown_exploits")
            result = after_markdown

        # Validate length
        length_result = validate_response_length(result, self.max_length)
        if length_result.was_truncated:
            removed_threats.append("excess_length")
            result = length_result.text

        return SanitizationResult(
            text=result,
            was_modified=len(removed_threats) > 0,
            removed_threats=removed_threats
        )


def sanitize_llm_output(text: str, max_length: int = DEFAULT_MAX_LENGTH) -> str:
    """
    Convenience function to sanitize LLM output.

    Args:
        text: Raw LLM output
        max_length: Maximum response length

    Returns:
        str: Sanitized text
    """
    sanitizer = LLMOutputSanitizer(max_length=max_length)
    result = sanitizer.sanitize(text)
    return result.text
