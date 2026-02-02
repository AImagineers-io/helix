"""
Output Encoding for XSS prevention and safe content rendering.

Provides:
- HTML entity encoding for web responses
- JSON string escaping for API responses
- LLM output sanitization
- Deep encoding for nested data structures

Used for:
- Encoding LLM-generated responses
- Encoding user-generated content
- API response sanitization
"""
import html
import json
import re
from typing import Any, Optional

# Dangerous patterns to remove from LLM output
DANGEROUS_PATTERNS = [
    (r"<script[^>]*>.*?</script>", re.IGNORECASE | re.DOTALL),
    (r"javascript:", re.IGNORECASE),
    (r"on\w+\s*=", re.IGNORECASE),  # onclick=, onerror=, etc.
]


def encode_html(text: Optional[str]) -> str:
    """
    Encode text for safe HTML rendering.

    Converts:
    - < to &lt;
    - > to &gt;
    - & to &amp;
    - " to &quot;
    - ' to &#x27;

    Args:
        text: Text to encode

    Returns:
        str: HTML-encoded text
    """
    if text is None:
        return ""
    if not text:
        return ""

    # Use html.escape which handles the main characters
    encoded = html.escape(str(text), quote=True)

    # Also encode single quotes which html.escape misses
    encoded = encoded.replace("'", "&#x27;")

    return encoded


def encode_json_string(text: str) -> str:
    """
    Escape a string for safe JSON inclusion.

    Escapes:
    - Backslashes
    - Quotes
    - Newlines
    - Tabs
    - Carriage returns

    Args:
        text: Text to escape

    Returns:
        str: JSON-escaped text
    """
    if not text:
        return text

    # Use json.dumps to handle escaping, then strip the quotes
    escaped = json.dumps(text)
    # Remove surrounding quotes added by json.dumps
    return escaped[1:-1]


def encode_for_api(data: Any, max_depth: int = 10) -> Any:
    """
    Recursively encode string values in a data structure for API output.

    Encodes all string values to prevent XSS when data is rendered
    in HTML contexts.

    Args:
        data: Data structure to encode (dict, list, or primitive)
        max_depth: Maximum recursion depth

    Returns:
        Encoded data structure
    """
    if max_depth <= 0:
        return data

    if isinstance(data, str):
        return encode_html(data)

    if isinstance(data, dict):
        return {
            key: encode_for_api(value, max_depth - 1)
            for key, value in data.items()
        }

    if isinstance(data, list):
        return [encode_for_api(item, max_depth - 1) for item in data]

    # Preserve other types (int, float, bool, None)
    return data


def encode_llm_output(text: str) -> str:
    """
    Encode LLM output for safe display.

    Removes dangerous content like:
    - Script tags
    - JavaScript URLs
    - Event handlers

    Preserves:
    - Markdown formatting
    - Code blocks (content encoded)

    Args:
        text: LLM-generated text

    Returns:
        str: Sanitized and encoded text
    """
    if not text:
        return ""

    result = text

    # Remove dangerous patterns
    for pattern, flags in DANGEROUS_PATTERNS:
        result = re.sub(pattern, "", result, flags=flags)

    # Encode HTML entities in the remaining text
    # But preserve markdown that doesn't contain HTML
    lines = result.split("\n")
    encoded_lines = []

    in_code_block = False
    for line in lines:
        # Track code blocks
        if line.strip().startswith("```"):
            in_code_block = not in_code_block
            encoded_lines.append(line)
            continue

        if in_code_block:
            # Encode content inside code blocks
            encoded_lines.append(encode_html(line))
        else:
            # Outside code blocks, encode HTML but preserve markdown
            # Encode < and > that aren't part of markdown
            encoded_line = line
            # Encode angle brackets
            encoded_line = encoded_line.replace("<", "&lt;")
            encoded_line = encoded_line.replace(">", "&gt;")
            encoded_lines.append(encoded_line)

    result = "\n".join(encoded_lines)

    # Check for javascript: in links
    result = re.sub(
        r"\[(.*?)\]\(javascript:[^)]*\)",
        r"[\1]()",
        result,
        flags=re.IGNORECASE
    )

    return result


class OutputEncoder:
    """
    Configurable output encoder for different contexts.

    Supports:
    - HTML context: Full HTML entity encoding
    - JSON context: JSON string escaping
    - LLM context: LLM-specific sanitization

    Example:
        encoder = OutputEncoder()
        safe_html = encoder.encode("<script>", context="html")
    """

    def __init__(self, default_context: str = "html"):
        """
        Initialize encoder.

        Args:
            default_context: Default encoding context
        """
        self.default_context = default_context

    def encode(self, text: str, context: Optional[str] = None) -> str:
        """
        Encode text for the specified context.

        Args:
            text: Text to encode
            context: Encoding context (html, json, llm)

        Returns:
            str: Encoded text
        """
        ctx = context or self.default_context

        if ctx == "json":
            return encode_json_string(text)
        elif ctx == "llm":
            return encode_llm_output(text)
        else:  # html (default)
            return encode_html(text)
