"""
PII Detection Service for identifying personal information in text.

Detects:
- Email addresses
- Phone numbers (US and international)
- Social Security Numbers (SSN)
- Credit card numbers

Returns match positions for precise redaction.
"""
import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class PIIMatch:
    """Represents a detected PII item."""
    type: str
    value: str
    start: int
    end: int
    confidence: float = 1.0


# Email pattern
EMAIL_PATTERN = re.compile(
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
)

# Phone patterns (US and international)
PHONE_PATTERNS = [
    # US format: (555) 123-4567 or 555-123-4567
    re.compile(r"\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"),
    # International: +1-555-123-4567 or +63 917 123 4567
    re.compile(r"\+\d{1,3}[-.\s]?\d{2,4}[-.\s]?\d{3,4}[-.\s]?\d{3,4}\b"),
]

# SSN pattern: 123-45-6789 or 123456789
SSN_PATTERN = re.compile(
    r"\b(?!000|666|9\d{2})\d{3}[-\s]?(?!00)\d{2}[-\s]?(?!0000)\d{4}\b"
)

# Credit card patterns (major card types)
CREDIT_CARD_PATTERNS = [
    # Visa: 4xxx xxxx xxxx xxxx
    re.compile(r"\b4\d{3}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b"),
    # Mastercard: 5[1-5]xx xxxx xxxx xxxx
    re.compile(r"\b5[1-5]\d{2}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b"),
    # Amex: 3[47]xx xxxxxx xxxxx
    re.compile(r"\b3[47]\d{2}[-\s]?\d{6}[-\s]?\d{5}\b"),
    # Generic 16-digit
    re.compile(r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b"),
]


def detect_emails(text: str) -> list[PIIMatch]:
    """
    Detect email addresses in text.

    Args:
        text: Text to analyze

    Returns:
        list: List of email matches
    """
    matches = []
    for match in EMAIL_PATTERN.finditer(text):
        matches.append(PIIMatch(
            type="email",
            value=match.group(),
            start=match.start(),
            end=match.end()
        ))
    return matches


def detect_phone_numbers(text: str) -> list[PIIMatch]:
    """
    Detect phone numbers in text.

    Args:
        text: Text to analyze

    Returns:
        list: List of phone matches
    """
    matches = []
    seen_positions = set()

    for pattern in PHONE_PATTERNS:
        for match in pattern.finditer(text):
            # Avoid duplicates from overlapping patterns
            if match.start() not in seen_positions:
                # Verify it's long enough to be a phone number
                digits = re.sub(r"[^\d]", "", match.group())
                if len(digits) >= 10:
                    matches.append(PIIMatch(
                        type="phone",
                        value=match.group(),
                        start=match.start(),
                        end=match.end()
                    ))
                    seen_positions.add(match.start())

    return matches


def detect_ssn(text: str) -> list[PIIMatch]:
    """
    Detect Social Security Numbers in text.

    Args:
        text: Text to analyze

    Returns:
        list: List of SSN matches
    """
    matches = []
    for match in SSN_PATTERN.finditer(text):
        # Additional validation: exclude invalid SSNs
        digits = re.sub(r"[^\d]", "", match.group())
        if len(digits) == 9:
            # Check for invalid patterns
            area = int(digits[:3])
            group = int(digits[3:5])
            serial = int(digits[5:])

            # Invalid areas: 000, 666, 900-999
            if area == 0 or area == 666 or area >= 900:
                continue
            # Invalid group or serial
            if group == 0 or serial == 0:
                continue

            matches.append(PIIMatch(
                type="ssn",
                value=match.group(),
                start=match.start(),
                end=match.end()
            ))

    return matches


def detect_credit_cards(text: str) -> list[PIIMatch]:
    """
    Detect credit card numbers in text.

    Uses basic Luhn algorithm validation.

    Args:
        text: Text to analyze

    Returns:
        list: List of credit card matches
    """
    matches = []
    seen_positions = set()

    for pattern in CREDIT_CARD_PATTERNS:
        for match in pattern.finditer(text):
            if match.start() not in seen_positions:
                # Extract digits
                digits = re.sub(r"[^\d]", "", match.group())

                # Basic validation: correct length
                if len(digits) >= 13 and len(digits) <= 19:
                    # Luhn algorithm check
                    if _luhn_check(digits):
                        matches.append(PIIMatch(
                            type="credit_card",
                            value=match.group(),
                            start=match.start(),
                            end=match.end()
                        ))
                        seen_positions.add(match.start())

    return matches


def _luhn_check(card_number: str) -> bool:
    """
    Validate credit card number using Luhn algorithm.

    Args:
        card_number: Card number (digits only)

    Returns:
        bool: True if valid
    """
    digits = [int(d) for d in card_number]
    odd_digits = digits[-1::-2]
    even_digits = digits[-2::-2]

    checksum = sum(odd_digits)
    for d in even_digits:
        checksum += sum(divmod(d * 2, 10))

    return checksum % 10 == 0


class PIIDetector:
    """
    Detects all types of PII in text.

    Combines detection of:
    - Email addresses
    - Phone numbers
    - SSNs
    - Credit card numbers
    """

    def __init__(self):
        """Initialize PII detector."""
        pass

    def detect(self, text: str) -> list[PIIMatch]:
        """
        Detect all PII in text.

        Args:
            text: Text to analyze

        Returns:
            list: All PII matches found
        """
        if not text:
            return []

        matches = []
        matches.extend(detect_emails(text))
        matches.extend(detect_phone_numbers(text))
        matches.extend(detect_ssn(text))
        matches.extend(detect_credit_cards(text))

        # Sort by position
        matches.sort(key=lambda m: m.start)

        return matches
