"""
Integration tests for Webhook Signature Validation (P12.4.4)

Tests webhook security including:
- Facebook X-Hub-Signature-256 validation
- Timing-safe comparison
- Invalid signature rejection
- Missing signature handling
"""
import pytest
import hmac
import hashlib

from core.webhook_security import (
    WebhookSignatureValidator,
    validate_facebook_signature,
    compute_signature,
    timing_safe_compare,
    WebhookValidationError,
)


class TestSignatureComputation:
    """Tests for signature computation."""

    def test_compute_sha256_signature(self):
        """Should compute SHA256 HMAC signature."""
        secret = "test_secret"
        payload = b'{"test": "data"}'

        signature = compute_signature(payload, secret)

        assert signature is not None
        assert signature.startswith("sha256=")

    def test_signature_is_deterministic(self):
        """Same inputs should produce same signature."""
        secret = "test_secret"
        payload = b'{"test": "data"}'

        sig1 = compute_signature(payload, secret)
        sig2 = compute_signature(payload, secret)

        assert sig1 == sig2

    def test_different_secrets_different_signatures(self):
        """Different secrets should produce different signatures."""
        payload = b'{"test": "data"}'

        sig1 = compute_signature(payload, "secret1")
        sig2 = compute_signature(payload, "secret2")

        assert sig1 != sig2

    def test_different_payloads_different_signatures(self):
        """Different payloads should produce different signatures."""
        secret = "test_secret"

        sig1 = compute_signature(b'{"a": 1}', secret)
        sig2 = compute_signature(b'{"a": 2}', secret)

        assert sig1 != sig2


class TestTimingSafeCompare:
    """Tests for timing-safe comparison."""

    def test_equal_strings_match(self):
        """Equal strings should return True."""
        assert timing_safe_compare("abc123", "abc123") is True

    def test_different_strings_dont_match(self):
        """Different strings should return False."""
        assert timing_safe_compare("abc123", "xyz789") is False

    def test_empty_strings_match(self):
        """Empty strings should match."""
        assert timing_safe_compare("", "") is True

    def test_different_lengths_dont_match(self):
        """Different length strings should return False."""
        assert timing_safe_compare("short", "much longer string") is False


class TestFacebookSignatureValidation:
    """Tests for Facebook webhook signature validation."""

    @pytest.fixture
    def secret(self):
        return "facebook_app_secret"

    @pytest.fixture
    def valid_payload(self):
        return b'{"object":"page","entry":[{"id":"123","messaging":[]}]}'

    def test_valid_signature_passes(self, secret, valid_payload):
        """Valid signature should pass validation."""
        # Compute actual signature
        expected_sig = hmac.new(
            secret.encode(),
            valid_payload,
            hashlib.sha256
        ).hexdigest()
        signature = f"sha256={expected_sig}"

        result = validate_facebook_signature(valid_payload, signature, secret)
        assert result is True

    def test_invalid_signature_fails(self, secret, valid_payload):
        """Invalid signature should fail validation."""
        invalid_signature = "sha256=invalid_signature_here"

        result = validate_facebook_signature(
            valid_payload,
            invalid_signature,
            secret
        )
        assert result is False

    def test_missing_signature_fails(self, secret, valid_payload):
        """Missing signature should fail validation."""
        result = validate_facebook_signature(valid_payload, None, secret)
        assert result is False

    def test_empty_signature_fails(self, secret, valid_payload):
        """Empty signature should fail validation."""
        result = validate_facebook_signature(valid_payload, "", secret)
        assert result is False

    def test_wrong_algorithm_fails(self, secret, valid_payload):
        """Wrong algorithm prefix should fail."""
        # Use sha1 prefix with sha256 content
        signature = "sha1=wrongalgorithm"

        result = validate_facebook_signature(valid_payload, signature, secret)
        assert result is False

    def test_tampered_payload_fails(self, secret):
        """Tampered payload should fail."""
        original = b'{"amount": 100}'
        tampered = b'{"amount": 999}'

        # Compute signature for original
        expected_sig = hmac.new(
            secret.encode(),
            original,
            hashlib.sha256
        ).hexdigest()
        signature = f"sha256={expected_sig}"

        # Validate against tampered
        result = validate_facebook_signature(tampered, signature, secret)
        assert result is False


class TestWebhookSignatureValidator:
    """Tests for WebhookSignatureValidator class."""

    @pytest.fixture
    def validator(self):
        """Create validator with test secret."""
        return WebhookSignatureValidator(
            secrets={
                "facebook": "fb_secret",
                "stripe": "stripe_secret",
            }
        )

    def test_validate_known_provider(self, validator):
        """Should validate known provider signature."""
        payload = b'{"event": "test"}'
        expected_sig = hmac.new(
            b"fb_secret",
            payload,
            hashlib.sha256
        ).hexdigest()
        signature = f"sha256={expected_sig}"

        result = validator.validate("facebook", payload, signature)
        assert result is True

    def test_validate_unknown_provider_raises(self, validator):
        """Should raise error for unknown provider."""
        with pytest.raises(WebhookValidationError) as exc:
            validator.validate("unknown", b"payload", "sig")

        assert "Unknown provider" in str(exc.value)

    def test_validate_returns_false_for_invalid(self, validator):
        """Should return False for invalid signature."""
        result = validator.validate("facebook", b"payload", "sha256=wrong")
        assert result is False

    def test_add_provider(self, validator):
        """Should be able to add new provider."""
        validator.add_provider("github", "github_secret")

        payload = b'{"event": "push"}'
        expected_sig = hmac.new(
            b"github_secret",
            payload,
            hashlib.sha256
        ).hexdigest()
        signature = f"sha256={expected_sig}"

        result = validator.validate("github", payload, signature)
        assert result is True


class TestWebhookValidationError:
    """Tests for WebhookValidationError exception."""

    def test_error_message(self):
        """Error should include message."""
        error = WebhookValidationError("Invalid signature")
        assert "Invalid signature" in str(error)

    def test_error_with_provider(self):
        """Error can include provider info."""
        error = WebhookValidationError("Invalid signature", provider="facebook")
        assert error.provider == "facebook"


class TestSignatureFormats:
    """Tests for different signature formats."""

    @pytest.fixture
    def validator(self):
        return WebhookSignatureValidator(secrets={"test": "secret"})

    def test_handles_sha256_prefix(self, validator):
        """Should handle sha256= prefix."""
        payload = b"data"
        sig = compute_signature(payload, "secret")

        result = validator.validate("test", payload, sig)
        assert result is True

    def test_handles_no_prefix(self, validator):
        """Should handle signature without prefix."""
        payload = b"data"
        raw_sig = hmac.new(b"secret", payload, hashlib.sha256).hexdigest()

        # Validator should be able to handle raw hex too
        result = validator.validate("test", payload, raw_sig)
        assert result is True

    def test_handles_uppercase_signature(self, validator):
        """Should handle uppercase hex signature."""
        payload = b"data"
        raw_sig = hmac.new(b"secret", payload, hashlib.sha256).hexdigest()

        result = validator.validate("test", payload, f"sha256={raw_sig.upper()}")
        assert result is True
