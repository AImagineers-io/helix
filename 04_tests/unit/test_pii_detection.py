"""
Unit tests for PII Detection and Redaction (P12.3.5)

Tests PII handling including:
- Email detection
- Phone number detection
- SSN pattern detection
- Credit card number detection
- Redaction modes (full/partial)
"""
import pytest

from services.pii_detector import (
    PIIDetector,
    PIIMatch,
    detect_emails,
    detect_phone_numbers,
    detect_ssn,
    detect_credit_cards,
)
from services.pii_redactor import (
    PIIRedactor,
    redact_pii,
    RedactionMode,
)


class TestEmailDetection:
    """Tests for email detection."""

    def test_detects_simple_email(self):
        """Should detect simple email addresses."""
        text = "Contact us at support@example.com"
        matches = detect_emails(text)
        assert len(matches) == 1
        assert matches[0].value == "support@example.com"

    def test_detects_multiple_emails(self):
        """Should detect multiple email addresses."""
        text = "Email john@test.com or jane@test.org"
        matches = detect_emails(text)
        assert len(matches) == 2

    def test_detects_complex_emails(self):
        """Should detect emails with subdomains and plus signs."""
        text = "user+tag@mail.subdomain.example.co.uk"
        matches = detect_emails(text)
        assert len(matches) == 1

    def test_no_false_positives(self):
        """Should not match non-email patterns."""
        text = "version 1.0 or @mention or invalid@"
        matches = detect_emails(text)
        assert len(matches) == 0


class TestPhoneNumberDetection:
    """Tests for phone number detection."""

    def test_detects_us_format(self):
        """Should detect US phone number formats."""
        text = "Call 555-123-4567 or (555) 123-4567"
        matches = detect_phone_numbers(text)
        assert len(matches) >= 1

    def test_detects_international(self):
        """Should detect international phone numbers."""
        text = "Call +1-555-123-4567 or +44 20 7946 0958"
        matches = detect_phone_numbers(text)
        assert len(matches) >= 1

    def test_detects_with_country_code(self):
        """Should detect numbers with country codes."""
        text = "Phone: +63 917 123 4567"
        matches = detect_phone_numbers(text)
        assert len(matches) >= 1

    def test_ignores_short_numbers(self):
        """Should not match numbers that are too short."""
        text = "Version 123 or code 4567"
        matches = detect_phone_numbers(text)
        assert len(matches) == 0


class TestSSNDetection:
    """Tests for Social Security Number detection."""

    def test_detects_ssn_format(self):
        """Should detect standard SSN format."""
        text = "SSN: 123-45-6789"
        matches = detect_ssn(text)
        assert len(matches) == 1
        assert "123-45-6789" in matches[0].value

    def test_detects_ssn_without_dashes(self):
        """Should detect SSN without dashes."""
        text = "SSN 123456789"
        matches = detect_ssn(text)
        assert len(matches) == 1

    def test_ignores_invalid_ssn(self):
        """Should not match invalid SSN patterns."""
        text = "Number 000-00-0000 is invalid"
        matches = detect_ssn(text)
        # 000-00-0000 is not a valid SSN
        assert len(matches) == 0


class TestCreditCardDetection:
    """Tests for credit card number detection."""

    def test_detects_visa(self):
        """Should detect Visa card numbers."""
        text = "Card: 4111111111111111"
        matches = detect_credit_cards(text)
        assert len(matches) == 1
        assert matches[0].type == "credit_card"

    def test_detects_mastercard(self):
        """Should detect Mastercard numbers."""
        text = "Pay with 5500000000000004"
        matches = detect_credit_cards(text)
        assert len(matches) == 1

    def test_detects_with_spaces(self):
        """Should detect card numbers with spaces."""
        text = "Card: 4111 1111 1111 1111"
        matches = detect_credit_cards(text)
        assert len(matches) == 1

    def test_detects_with_dashes(self):
        """Should detect card numbers with dashes."""
        text = "Card: 4111-1111-1111-1111"
        matches = detect_credit_cards(text)
        assert len(matches) == 1


class TestPIIDetector:
    """Tests for the full PII detector."""

    @pytest.fixture
    def detector(self):
        """Create PII detector instance."""
        return PIIDetector()

    def test_detect_all_types(self, detector):
        """Should detect all PII types."""
        text = """
        Email: john@example.com
        Phone: 555-123-4567
        SSN: 123-45-6789
        Card: 4111111111111111
        """
        matches = detector.detect(text)
        types = {m.type for m in matches}
        assert "email" in types
        assert "phone" in types
        assert "ssn" in types
        assert "credit_card" in types

    def test_returns_positions(self, detector):
        """Should return match positions."""
        text = "Email: test@example.com here"
        matches = detector.detect(text)
        assert matches[0].start >= 0
        assert matches[0].end > matches[0].start

    def test_empty_text(self, detector):
        """Empty text should return no matches."""
        matches = detector.detect("")
        assert matches == []


class TestPIIRedactor:
    """Tests for PII redaction."""

    @pytest.fixture
    def redactor(self):
        """Create PII redactor instance."""
        return PIIRedactor()

    def test_full_redaction(self, redactor):
        """Full redaction should replace entire value."""
        text = "Email: john@example.com"
        result = redactor.redact(text, mode=RedactionMode.FULL)
        assert "john@example.com" not in result
        assert "[REDACTED]" in result or "[EMAIL]" in result

    def test_partial_redaction(self, redactor):
        """Partial redaction should mask part of value."""
        text = "Email: john@example.com"
        result = redactor.redact(text, mode=RedactionMode.PARTIAL)
        assert "john@example.com" not in result
        # Should show some characters but masked
        assert "***" in result or "..." in result

    def test_redact_preserves_context(self, redactor):
        """Redaction should preserve surrounding text."""
        text = "Contact john@example.com for help"
        result = redactor.redact(text)
        assert "Contact" in result
        assert "for help" in result


class TestRedactPII:
    """Tests for the convenience function."""

    def test_redact_pii_default(self):
        """Default redaction should work."""
        text = "My email is test@example.com"
        result = redact_pii(text)
        assert "test@example.com" not in result

    def test_redact_pii_returns_original_if_no_pii(self):
        """Text without PII should be unchanged."""
        text = "No personal information here"
        result = redact_pii(text)
        assert result == text
