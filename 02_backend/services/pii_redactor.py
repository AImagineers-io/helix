"""
PII Redaction Service for removing personal information from text.

Provides:
- Full redaction: Replace with [REDACTED]
- Partial redaction: Mask with asterisks
- Type-specific redaction labels

Works with PIIDetector to locate and redact PII.
"""
from dataclasses import dataclass
from enum import Enum
from typing import Optional

from services.pii_detector import PIIDetector, PIIMatch


class RedactionMode(Enum):
    """Redaction mode options."""
    FULL = "full"  # Replace entirely with [REDACTED]
    PARTIAL = "partial"  # Mask most characters with ***


# Type-specific redaction labels
REDACTION_LABELS = {
    "email": "[EMAIL]",
    "phone": "[PHONE]",
    "ssn": "[SSN]",
    "credit_card": "[CARD]",
    "default": "[REDACTED]",
}


def _mask_partial(value: str, pii_type: str) -> str:
    """
    Create partial mask of PII value.

    Shows first and last characters with asterisks in between.

    Args:
        value: Original PII value
        pii_type: Type of PII

    Returns:
        str: Masked value
    """
    if len(value) <= 4:
        return "***"

    if pii_type == "email":
        # Show first 2 chars and domain
        at_pos = value.find("@")
        if at_pos > 2:
            return value[:2] + "***" + value[at_pos:]
        return value[:1] + "***" + value[-4:]

    if pii_type == "phone":
        # Show last 4 digits
        return "***-***-" + value[-4:]

    if pii_type == "ssn":
        # Show last 4 digits
        return "***-**-" + value[-4:]

    if pii_type == "credit_card":
        # Show last 4 digits
        return "****-****-****-" + value[-4:]

    # Default: show first and last char
    return value[0] + "***" + value[-1]


@dataclass
class RedactionResult:
    """Result of PII redaction."""
    text: str
    redactions_made: int
    pii_types_found: list[str]


class PIIRedactor:
    """
    Redacts PII from text.

    Uses PIIDetector to find PII, then replaces with
    redaction text based on the configured mode.
    """

    def __init__(self, detector: Optional[PIIDetector] = None):
        """
        Initialize PII redactor.

        Args:
            detector: PII detector to use (creates new one if not provided)
        """
        self.detector = detector or PIIDetector()

    def redact(
        self,
        text: str,
        mode: RedactionMode = RedactionMode.FULL
    ) -> str:
        """
        Redact PII from text.

        Args:
            text: Text containing PII
            mode: Redaction mode (full or partial)

        Returns:
            str: Text with PII redacted
        """
        if not text:
            return text

        matches = self.detector.detect(text)

        if not matches:
            return text

        # Sort matches by position (reverse order to preserve indices)
        sorted_matches = sorted(matches, key=lambda m: m.start, reverse=True)

        result = text
        for match in sorted_matches:
            if mode == RedactionMode.FULL:
                replacement = REDACTION_LABELS.get(
                    match.type,
                    REDACTION_LABELS["default"]
                )
            else:
                replacement = _mask_partial(match.value, match.type)

            result = result[:match.start] + replacement + result[match.end:]

        return result

    def redact_with_details(
        self,
        text: str,
        mode: RedactionMode = RedactionMode.FULL
    ) -> RedactionResult:
        """
        Redact PII and return detailed result.

        Args:
            text: Text containing PII
            mode: Redaction mode

        Returns:
            RedactionResult: Redacted text with metadata
        """
        if not text:
            return RedactionResult(
                text="",
                redactions_made=0,
                pii_types_found=[]
            )

        matches = self.detector.detect(text)

        if not matches:
            return RedactionResult(
                text=text,
                redactions_made=0,
                pii_types_found=[]
            )

        redacted = self.redact(text, mode)
        pii_types = list(set(m.type for m in matches))

        return RedactionResult(
            text=redacted,
            redactions_made=len(matches),
            pii_types_found=pii_types
        )


def redact_pii(
    text: str,
    mode: RedactionMode = RedactionMode.FULL
) -> str:
    """
    Convenience function to redact PII from text.

    Args:
        text: Text to redact
        mode: Redaction mode

    Returns:
        str: Text with PII redacted
    """
    redactor = PIIRedactor()
    return redactor.redact(text, mode)
