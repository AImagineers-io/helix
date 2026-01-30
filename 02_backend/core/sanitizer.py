"""
Input sanitization utilities for Helix security.

This module provides comprehensive input sanitization to protect against:
- Cross-Site Scripting (XSS) attacks
- SQL injection patterns
- Path traversal attacks
- Null byte injection
- Other common injection attacks

Usage:
    from core.sanitizer import sanitize_input, is_safe_string

    # Sanitize user input
    safe_text = sanitize_input(user_input)

    # Check if input is safe
    if not is_safe_string(user_input):
        raise ValueError("Unsafe input detected")

Security Notes:
- Always sanitize user input before storing or displaying
- Use parameterized queries for database operations (primary defense)
- This module provides defense-in-depth, not a replacement for proper escaping
"""
import html
import re
from typing import Final
from urllib.parse import unquote


# XSS patterns to remove
XSS_PATTERNS: Final[list[re.Pattern]] = [
    # Script tags (including nested attempts)
    re.compile(r'<\s*script[^>]*>.*?<\s*/\s*script\s*>', re.IGNORECASE | re.DOTALL),
    re.compile(r'<\s*script[^>]*>', re.IGNORECASE),
    re.compile(r'<\s*/\s*script\s*>', re.IGNORECASE),
    # Event handlers
    re.compile(r'\s*on\w+\s*=\s*["\'][^"\']*["\']', re.IGNORECASE),
    re.compile(r'\s*on\w+\s*=\s*[^\s>]+', re.IGNORECASE),
    # JavaScript URLs
    re.compile(r'javascript\s*:', re.IGNORECASE),
    # VBScript URLs (legacy IE)
    re.compile(r'vbscript\s*:', re.IGNORECASE),
    # Data URLs with dangerous content
    re.compile(r'data\s*:[^,]*;base64[^"\'>\s]*', re.IGNORECASE),
    # SVG event handlers
    re.compile(r'<\s*svg[^>]*on\w+\s*=', re.IGNORECASE),
    # Object/embed tags
    re.compile(r'<\s*object[^>]*>', re.IGNORECASE),
    re.compile(r'<\s*embed[^>]*>', re.IGNORECASE),
    # iframes
    re.compile(r'<\s*iframe[^>]*>', re.IGNORECASE),
    # Style with expression (IE)
    re.compile(r'expression\s*\([^)]*\)', re.IGNORECASE),
]

# SQL injection patterns
SQL_INJECTION_PATTERNS: Final[list[re.Pattern]] = [
    # UNION-based injection
    re.compile(r'\bunion\b.*\bselect\b', re.IGNORECASE),
    # DROP/DELETE/TRUNCATE attacks
    re.compile(r'\bdrop\b.*\btable\b', re.IGNORECASE),
    re.compile(r'\bdelete\b.*\bfrom\b', re.IGNORECASE),
    re.compile(r'\btruncate\b.*\btable\b', re.IGNORECASE),
    # Comment-based injection
    re.compile(r'--\s*$', re.MULTILINE),
    re.compile(r'/\*.*\*/', re.DOTALL),
    # Boolean-based injection
    re.compile(r"'\s*or\s*'[^']*'\s*=\s*'", re.IGNORECASE),
    re.compile(r"'\s*or\s+\d+\s*=\s*\d+", re.IGNORECASE),
    re.compile(r'"\s*or\s*"[^"]*"\s*=\s*"', re.IGNORECASE),
    # Stacked queries
    re.compile(r';\s*(drop|delete|insert|update|create|alter)\b', re.IGNORECASE),
    # Information schema access
    re.compile(r'\binformation_schema\b', re.IGNORECASE),
    # Sleep/benchmark (timing attacks)
    re.compile(r'\b(sleep|benchmark|waitfor)\s*\(', re.IGNORECASE),
]

# Path traversal patterns
PATH_TRAVERSAL_PATTERNS: Final[list[re.Pattern]] = [
    # Basic traversal
    re.compile(r'\.\.[\\/]'),
    re.compile(r'\.\.%2[fF]'),
    re.compile(r'\.\.%5[cC]'),
    # Double-encoded
    re.compile(r'\.\.%25(?:2[fF]|5[cC])'),
    # Unicode-encoded
    re.compile(r'\.\.[%/\\]'),
    # Null byte followed by extension
    re.compile(r'%00'),
]


def sanitize_input(text: str) -> str:
    """Sanitize user input by removing dangerous patterns.

    Removes XSS vectors, null bytes, and other dangerous content while
    preserving safe text content including unicode characters.

    Args:
        text: Raw user input to sanitize.

    Returns:
        Sanitized text with dangerous patterns removed.

    Examples:
        >>> sanitize_input("<script>alert(1)</script>")
        ''
        >>> sanitize_input("Hello, world!")
        'Hello, world!'
    """
    if not text:
        return text

    result = text

    # Remove null bytes
    result = result.replace('\x00', '')
    result = result.replace('%00', '')

    # Remove XSS patterns
    for pattern in XSS_PATTERNS:
        result = pattern.sub('', result)

    # Clean up any remaining script-like fragments
    # Handle nested/obfuscated script tags
    while '<script' in result.lower() or '</script' in result.lower():
        result = re.sub(r'<[/]?script[^>]*>', '', result, flags=re.IGNORECASE)

    return result.strip()


def contains_sql_injection(text: str) -> bool:
    """Check if text contains SQL injection patterns.

    Note: This is a heuristic check for logging/alerting purposes.
    Always use parameterized queries as the primary defense.

    Args:
        text: Text to check for SQL injection patterns.

    Returns:
        True if SQL injection patterns are detected, False otherwise.

    Examples:
        >>> contains_sql_injection("'; DROP TABLE users;--")
        True
        >>> contains_sql_injection("What is the return policy?")
        False
    """
    if not text:
        return False

    for pattern in SQL_INJECTION_PATTERNS:
        if pattern.search(text):
            return True

    return False


def contains_path_traversal(text: str) -> bool:
    """Check if text contains path traversal patterns.

    Checks for various encodings of directory traversal attempts.

    Args:
        text: Text to check for path traversal patterns.

    Returns:
        True if path traversal patterns are detected, False otherwise.

    Examples:
        >>> contains_path_traversal("../../../etc/passwd")
        True
        >>> contains_path_traversal("documents/report.pdf")
        False
    """
    if not text:
        return False

    # Check original text
    for pattern in PATH_TRAVERSAL_PATTERNS:
        if pattern.search(text):
            return True

    # Check URL-decoded text (handles single encoding)
    try:
        decoded = unquote(text)
        if decoded != text:
            for pattern in PATH_TRAVERSAL_PATTERNS:
                if pattern.search(decoded):
                    return True

            # Check double-decoded (handles double encoding)
            double_decoded = unquote(decoded)
            if double_decoded != decoded:
                for pattern in PATH_TRAVERSAL_PATTERNS:
                    if pattern.search(double_decoded):
                        return True
    except Exception:
        pass

    return False


def encode_for_html(text: str) -> str:
    """Encode text for safe HTML output.

    Converts special HTML characters to their entity equivalents to prevent
    XSS when displaying user content in HTML.

    Args:
        text: Text to encode for HTML output.

    Returns:
        HTML-encoded text safe for display.

    Examples:
        >>> encode_for_html("<script>alert(1)</script>")
        '&lt;script&gt;alert(1)&lt;/script&gt;'
    """
    return html.escape(text, quote=True)


def is_safe_string(text: str) -> bool:
    """Check if a string is safe from common injection attacks.

    Performs comprehensive safety checks including XSS, SQL injection,
    and path traversal detection.

    Args:
        text: Text to validate.

    Returns:
        True if the text is considered safe, False otherwise.

    Examples:
        >>> is_safe_string("Hello, world!")
        True
        >>> is_safe_string("<script>alert(1)</script>")
        False
    """
    if not text:
        return True

    # Check for XSS patterns
    sanitized = sanitize_input(text)
    if sanitized != text:
        return False

    # Check for SQL injection
    if contains_sql_injection(text):
        return False

    # Check for path traversal
    if contains_path_traversal(text):
        return False

    return True


def sanitize_for_database(text: str) -> str:
    """Sanitize text before database storage.

    Note: This is defense-in-depth. Always use parameterized queries.

    Args:
        text: Text to sanitize for database storage.

    Returns:
        Sanitized text safe for storage.
    """
    return sanitize_input(text)


def sanitize_filename(filename: str) -> str:
    """Sanitize a filename for safe file system operations.

    Removes path separators, traversal attempts, null bytes, and other
    dangerous characters from filenames.

    Args:
        filename: Filename to sanitize.

    Returns:
        Sanitized filename safe for file system operations.

    Examples:
        >>> sanitize_filename("../../../etc/passwd")
        'etcpasswd'
        >>> sanitize_filename("report_2024.pdf")
        'report_2024.pdf'
    """
    if not filename:
        return filename

    result = filename

    # Remove null bytes
    result = result.replace('\x00', '')
    result = result.replace('%00', '')

    # Remove path separators and traversal
    result = result.replace('..', '')
    result = result.replace('/', '')
    result = result.replace('\\', '')

    # Remove URL-encoded separators
    result = re.sub(r'%2[fF]', '', result)  # /
    result = re.sub(r'%5[cC]', '', result)  # \

    # Remove control characters
    result = re.sub(r'[\x00-\x1f\x7f]', '', result)

    # Remove potentially dangerous characters
    result = re.sub(r'[<>:"|?*]', '', result)

    return result.strip()
