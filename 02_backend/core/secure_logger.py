"""
Secure Logging with data masking.

Provides:
- API key masking
- Token masking
- PII masking in logs
- Structured JSON logs
- Sensitive key detection

Use this logger for all production logging to prevent
secrets and PII from appearing in log files.
"""
import re
import json
import logging
from copy import deepcopy
from datetime import datetime, timezone
from typing import Any, Optional


# Sensitive key patterns
SENSITIVE_KEY_PATTERNS = [
    r"password",
    r"passwd",
    r"secret",
    r"token",
    r"api[_-]?key",
    r"apikey",
    r"auth",
    r"credential",
    r"private[_-]?key",
]

# PII patterns
EMAIL_PATTERN = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
PHONE_PATTERN = re.compile(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b')
SSN_PATTERN = re.compile(r'\b\d{3}[-]?\d{2}[-]?\d{4}\b')


def mask_api_key(api_key: Optional[str]) -> str:
    """
    Mask API key showing only last 4 characters.

    Args:
        api_key: API key to mask

    Returns:
        str: Masked API key
    """
    if not api_key:
        return "[NONE]"

    if len(api_key) <= 4:
        return "***"

    return f"***{api_key[-4:]}"


def mask_token(token: Optional[str]) -> str:
    """
    Mask token showing only first 8 characters.

    Args:
        token: Token to mask

    Returns:
        str: Masked token
    """
    if not token:
        return "[NONE]"

    if len(token) <= 8:
        return f"{token[:2]}***"

    return f"{token[:8]}***"


def mask_pii(text: str) -> str:
    """
    Mask PII in text.

    Args:
        text: Text that may contain PII

    Returns:
        str: Text with PII masked
    """
    if not text:
        return text

    # Mask emails
    result = EMAIL_PATTERN.sub("[EMAIL]", text)

    # Mask phone numbers
    result = PHONE_PATTERN.sub("[PHONE]", result)

    # Mask SSN
    result = SSN_PATTERN.sub("[SSN]", result)

    return result


class LogMasker:
    """
    Masks sensitive data in log entries.

    Automatically detects and masks:
    - API keys
    - Tokens
    - Passwords
    - Secrets
    - PII
    """

    def __init__(self, additional_patterns: Optional[list[str]] = None):
        """
        Initialize log masker.

        Args:
            additional_patterns: Additional sensitive key patterns
        """
        self._patterns = SENSITIVE_KEY_PATTERNS.copy()
        if additional_patterns:
            self._patterns.extend(additional_patterns)

        self._compiled_patterns = [
            re.compile(p, re.IGNORECASE) for p in self._patterns
        ]

    def is_sensitive_key(self, key: str) -> bool:
        """
        Check if key is sensitive.

        Args:
            key: Key name to check

        Returns:
            bool: True if key is sensitive
        """
        key_lower = key.lower()
        for pattern in self._compiled_patterns:
            if pattern.search(key_lower):
                return True
        return False

    def mask_value(self, key: str, value: Any) -> Any:
        """
        Mask value if key is sensitive.

        Args:
            key: Key name
            value: Value to potentially mask

        Returns:
            Any: Masked value if sensitive, original otherwise
        """
        if not self.is_sensitive_key(key):
            return value

        if isinstance(value, str):
            if "key" in key.lower():
                return mask_api_key(value)
            elif "token" in key.lower():
                return mask_token(value)
            else:
                return "***MASKED***"

        return "***MASKED***"

    def mask_dict(self, data: dict) -> dict:
        """
        Mask sensitive values in dictionary.

        Args:
            data: Dictionary to mask

        Returns:
            dict: Dictionary with masked values
        """
        result = {}

        for key, value in data.items():
            if isinstance(value, dict):
                result[key] = self.mask_dict(value)
            elif isinstance(value, list):
                result[key] = self._mask_list(key, value)
            else:
                result[key] = self.mask_value(key, value)

        return result

    def _mask_list(self, key: str, items: list) -> list:
        """Mask items in a list."""
        if self.is_sensitive_key(key):
            return ["***MASKED***" for _ in items]

        return [
            self.mask_dict(item) if isinstance(item, dict) else item
            for item in items
        ]


class SecureLogger:
    """
    Secure logger that masks sensitive data.

    Creates structured JSON logs with automatic masking
    of secrets and PII.
    """

    def __init__(self, name: str, masker: Optional[LogMasker] = None):
        """
        Initialize secure logger.

        Args:
            name: Logger name
            masker: Log masker instance
        """
        self.name = name
        self._masker = masker or LogMasker()
        self._logger = logging.getLogger(name)

    def create_log_entry(
        self,
        level: str,
        message: str,
        extra: Optional[dict] = None
    ) -> dict:
        """
        Create structured log entry.

        Args:
            level: Log level
            message: Log message
            extra: Additional fields

        Returns:
            dict: Structured log entry
        """
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": level,
            "logger": self.name,
            "message": mask_pii(message),
        }

        if extra:
            masked_extra = self._masker.mask_dict(extra)
            entry.update(masked_extra)

        return entry

    def info(self, message: str, **kwargs):
        """Log info message."""
        entry = self.create_log_entry("INFO", message, kwargs)
        self._logger.info(json.dumps(entry))

    def warning(self, message: str, **kwargs):
        """Log warning message."""
        entry = self.create_log_entry("WARNING", message, kwargs)
        self._logger.warning(json.dumps(entry))

    def error(self, message: str, **kwargs):
        """Log error message."""
        entry = self.create_log_entry("ERROR", message, kwargs)
        self._logger.error(json.dumps(entry))

    def debug(self, message: str, **kwargs):
        """Log debug message."""
        entry = self.create_log_entry("DEBUG", message, kwargs)
        self._logger.debug(json.dumps(entry))


def create_secure_logger(name: str) -> SecureLogger:
    """
    Create a secure logger instance.

    Args:
        name: Logger name

    Returns:
        SecureLogger: Configured secure logger
    """
    return SecureLogger(name)
