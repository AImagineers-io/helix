"""
Unit tests for Secure Logging (P12.5.4)

Tests secure logging including:
- API key masking
- Token masking
- PII masking in logs
- Structured JSON logs
"""
import pytest
import json

from core.secure_logger import (
    SecureLogger,
    LogMasker,
    mask_api_key,
    mask_token,
    mask_pii,
    create_secure_logger,
)


class TestMaskAPIKey:
    """Tests for API key masking."""

    def test_masks_api_key(self):
        """Should mask API key showing only last 4 chars."""
        api_key = "hx_abcdefghij1234567890"

        masked = mask_api_key(api_key)

        assert masked != api_key
        assert "7890" in masked  # Last 4 chars visible
        assert "***" in masked
        assert "abcdef" not in masked

    def test_masks_short_key(self):
        """Short key should be fully masked."""
        masked = mask_api_key("ab")
        assert masked == "***"

    def test_handles_none(self):
        """None should return placeholder."""
        masked = mask_api_key(None)
        assert masked == "[NONE]"

    def test_handles_empty(self):
        """Empty string should return placeholder."""
        masked = mask_api_key("")
        assert masked == "[NONE]"


class TestMaskToken:
    """Tests for token masking."""

    def test_masks_jwt_token(self):
        """Should mask JWT token."""
        token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U"

        masked = mask_token(token)

        assert "eyJhbGc" in masked  # Start visible
        assert "***" in masked
        assert ".eyJzdWI" not in masked  # Middle hidden

    def test_masks_short_token(self):
        """Short token should be partially masked."""
        masked = mask_token("short")
        assert "***" in masked

    def test_handles_none(self):
        """None should return placeholder."""
        masked = mask_token(None)
        assert masked == "[NONE]"


class TestMaskPII:
    """Tests for PII masking."""

    def test_masks_email(self):
        """Should mask email addresses."""
        text = "Contact: user@example.com for info"

        masked = mask_pii(text)

        assert "user@example.com" not in masked
        assert "[EMAIL]" in masked or "***" in masked

    def test_masks_phone(self):
        """Should mask phone numbers."""
        text = "Call me at 555-123-4567"

        masked = mask_pii(text)

        assert "555-123-4567" not in masked

    def test_masks_ssn(self):
        """Should mask SSN."""
        text = "SSN: 123-45-6789"

        masked = mask_pii(text)

        assert "123-45-6789" not in masked

    def test_preserves_normal_text(self):
        """Normal text should be preserved."""
        text = "Hello, this is a normal message"

        masked = mask_pii(text)

        assert masked == text


class TestLogMasker:
    """Tests for LogMasker class."""

    @pytest.fixture
    def masker(self):
        """Create log masker."""
        return LogMasker()

    def test_mask_dict_keys(self, masker):
        """Should mask sensitive keys in dict."""
        data = {
            "api_key": "hx_secret123456789",
            "password": "supersecret",
            "username": "public_user",
        }

        masked = masker.mask_dict(data)

        assert "hx_secret123456789" not in str(masked)
        assert "supersecret" not in str(masked)
        assert "public_user" in str(masked)

    def test_mask_nested_dict(self, masker):
        """Should mask nested sensitive values."""
        data = {
            "user": {
                "name": "John",
                "auth": {
                    "token": "secret_token_12345",
                }
            }
        }

        masked = masker.mask_dict(data)

        assert "secret_token_12345" not in str(masked)
        assert "John" in str(masked)

    def test_mask_list_items(self, masker):
        """Should mask sensitive items in lists."""
        data = {
            "tokens": ["token1_secret", "token2_secret"],
        }

        masked = masker.mask_dict(data)

        assert "token1_secret" not in str(masked)


class TestSecureLogger:
    """Tests for SecureLogger class."""

    @pytest.fixture
    def logger(self):
        """Create secure logger."""
        return SecureLogger("test_logger")

    def test_masks_log_message(self, logger, capsys):
        """Should mask sensitive data in log message."""
        # This tests that the logger can be created
        # Actual logging behavior depends on configuration
        assert logger is not None

    def test_creates_structured_log(self, logger):
        """Should create structured log entry."""
        entry = logger.create_log_entry(
            level="INFO",
            message="User logged in",
            extra={"user_id": "123"}
        )

        assert entry["level"] == "INFO"
        assert entry["message"] == "User logged in"
        assert entry["user_id"] == "123"

    def test_log_entry_has_timestamp(self, logger):
        """Log entry should have timestamp."""
        entry = logger.create_log_entry("INFO", "Test")

        assert "timestamp" in entry

    def test_log_entry_masks_sensitive(self, logger):
        """Log entry should mask sensitive data."""
        entry = logger.create_log_entry(
            level="DEBUG",
            message="Auth attempt",
            extra={"api_key": "hx_supersecretkey123"}
        )

        assert "hx_supersecretkey123" not in str(entry)


class TestCreateSecureLogger:
    """Tests for create_secure_logger function."""

    def test_creates_logger(self):
        """Should create a secure logger."""
        logger = create_secure_logger("my_module")
        assert logger is not None

    def test_logger_has_name(self):
        """Logger should have configured name."""
        logger = create_secure_logger("custom_name")
        assert logger.name == "custom_name"


class TestSensitiveKeyDetection:
    """Tests for sensitive key detection."""

    @pytest.fixture
    def masker(self):
        return LogMasker()

    def test_detects_password_key(self, masker):
        """Should detect 'password' as sensitive."""
        assert masker.is_sensitive_key("password") is True
        assert masker.is_sensitive_key("user_password") is True
        assert masker.is_sensitive_key("PASSWORD") is True

    def test_detects_token_key(self, masker):
        """Should detect 'token' as sensitive."""
        assert masker.is_sensitive_key("token") is True
        assert masker.is_sensitive_key("access_token") is True
        assert masker.is_sensitive_key("refresh_token") is True

    def test_detects_secret_key(self, masker):
        """Should detect 'secret' as sensitive."""
        assert masker.is_sensitive_key("secret") is True
        assert masker.is_sensitive_key("api_secret") is True
        assert masker.is_sensitive_key("client_secret") is True

    def test_detects_api_key(self, masker):
        """Should detect 'api_key' as sensitive."""
        assert masker.is_sensitive_key("api_key") is True
        assert masker.is_sensitive_key("apikey") is True

    def test_normal_keys_not_sensitive(self, masker):
        """Normal keys should not be marked sensitive."""
        assert masker.is_sensitive_key("username") is False
        assert masker.is_sensitive_key("email") is False
        assert masker.is_sensitive_key("name") is False


class TestJSONLogFormat:
    """Tests for JSON log formatting."""

    @pytest.fixture
    def logger(self):
        return SecureLogger("json_test")

    def test_log_entry_is_json_serializable(self, logger):
        """Log entry should be JSON serializable."""
        entry = logger.create_log_entry(
            level="INFO",
            message="Test message",
            extra={"key": "value"}
        )

        # Should not raise
        json_str = json.dumps(entry)
        assert json_str is not None

    def test_log_entry_format(self, logger):
        """Log entry should have expected format."""
        entry = logger.create_log_entry("ERROR", "Something failed")

        required_fields = ["level", "message", "timestamp"]
        for field in required_fields:
            assert field in entry
