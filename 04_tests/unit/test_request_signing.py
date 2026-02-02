"""
Unit tests for API Request Signing (P12.4.5)

Tests request signing including:
- HMAC signature for internal API calls
- Timestamp validation
- Replay attack prevention
- Signature verification
"""
import pytest
import time

from services.http_client import (
    RequestSigner,
    sign_request,
    verify_request_signature,
    SignatureConfig,
    SignatureVerificationError,
)


class TestSignatureConfig:
    """Tests for signature configuration."""

    def test_default_config(self):
        """Default config should have sensible defaults."""
        config = SignatureConfig()
        assert config.timestamp_tolerance_seconds == 300  # 5 minutes
        assert config.algorithm == "sha256"

    def test_custom_tolerance(self):
        """Custom tolerance should be accepted."""
        config = SignatureConfig(timestamp_tolerance_seconds=60)
        assert config.timestamp_tolerance_seconds == 60


class TestRequestSigner:
    """Tests for RequestSigner class."""

    @pytest.fixture
    def signer(self):
        """Create request signer."""
        return RequestSigner(secret="test_secret")

    def test_sign_returns_headers(self, signer):
        """Sign should return headers dict."""
        headers = signer.sign(
            method="POST",
            url="/api/endpoint",
            body=b'{"data": "value"}'
        )

        assert "X-Signature" in headers
        assert "X-Timestamp" in headers

    def test_signature_includes_timestamp(self, signer):
        """Signature should include timestamp header."""
        headers = signer.sign("GET", "/api/test", b"")

        timestamp = int(headers["X-Timestamp"])
        assert timestamp > 0
        assert abs(timestamp - int(time.time())) < 5

    def test_signature_is_deterministic_for_same_inputs(self, signer):
        """Same inputs with same timestamp should produce same signature."""
        # Fix timestamp for test
        timestamp = str(int(time.time()))

        sig1 = signer._compute_signature(
            method="POST",
            url="/api/test",
            body=b"data",
            timestamp=timestamp
        )
        sig2 = signer._compute_signature(
            method="POST",
            url="/api/test",
            body=b"data",
            timestamp=timestamp
        )

        assert sig1 == sig2

    def test_different_methods_different_signatures(self, signer):
        """Different HTTP methods should produce different signatures."""
        timestamp = str(int(time.time()))

        sig_get = signer._compute_signature("GET", "/api", b"", timestamp)
        sig_post = signer._compute_signature("POST", "/api", b"", timestamp)

        assert sig_get != sig_post

    def test_different_urls_different_signatures(self, signer):
        """Different URLs should produce different signatures."""
        timestamp = str(int(time.time()))

        sig1 = signer._compute_signature("GET", "/api/a", b"", timestamp)
        sig2 = signer._compute_signature("GET", "/api/b", b"", timestamp)

        assert sig1 != sig2

    def test_different_bodies_different_signatures(self, signer):
        """Different bodies should produce different signatures."""
        timestamp = str(int(time.time()))

        sig1 = signer._compute_signature("POST", "/api", b"body1", timestamp)
        sig2 = signer._compute_signature("POST", "/api", b"body2", timestamp)

        assert sig1 != sig2


class TestSignatureVerification:
    """Tests for signature verification."""

    @pytest.fixture
    def signer(self):
        return RequestSigner(secret="verification_secret")

    def test_valid_signature_passes(self, signer):
        """Valid signature should pass verification."""
        headers = signer.sign("POST", "/api/test", b'{"key": "value"}')

        result = signer.verify(
            method="POST",
            url="/api/test",
            body=b'{"key": "value"}',
            signature=headers["X-Signature"],
            timestamp=headers["X-Timestamp"]
        )

        assert result is True

    def test_invalid_signature_fails(self, signer):
        """Invalid signature should fail verification."""
        result = signer.verify(
            method="POST",
            url="/api/test",
            body=b"data",
            signature="invalid_signature",
            timestamp=str(int(time.time()))
        )

        assert result is False

    def test_tampered_body_fails(self, signer):
        """Tampered body should fail verification."""
        headers = signer.sign("POST", "/api/test", b"original")

        result = signer.verify(
            method="POST",
            url="/api/test",
            body=b"tampered",
            signature=headers["X-Signature"],
            timestamp=headers["X-Timestamp"]
        )

        assert result is False

    def test_tampered_url_fails(self, signer):
        """Tampered URL should fail verification."""
        headers = signer.sign("POST", "/api/original", b"data")

        result = signer.verify(
            method="POST",
            url="/api/tampered",
            body=b"data",
            signature=headers["X-Signature"],
            timestamp=headers["X-Timestamp"]
        )

        assert result is False


class TestReplayPrevention:
    """Tests for replay attack prevention."""

    @pytest.fixture
    def signer(self):
        config = SignatureConfig(timestamp_tolerance_seconds=60)
        return RequestSigner(secret="replay_secret", config=config)

    def test_recent_timestamp_passes(self, signer):
        """Recent timestamp should pass."""
        headers = signer.sign("GET", "/api", b"")

        result = signer.verify(
            method="GET",
            url="/api",
            body=b"",
            signature=headers["X-Signature"],
            timestamp=headers["X-Timestamp"]
        )

        assert result is True

    def test_old_timestamp_fails(self, signer):
        """Old timestamp (outside tolerance) should fail."""
        old_timestamp = str(int(time.time()) - 120)  # 2 minutes ago

        sig = signer._compute_signature("GET", "/api", b"", old_timestamp)

        with pytest.raises(SignatureVerificationError) as exc:
            signer.verify_or_raise(
                method="GET",
                url="/api",
                body=b"",
                signature=sig,
                timestamp=old_timestamp
            )

        assert "expired" in str(exc.value).lower()

    def test_future_timestamp_fails(self, signer):
        """Future timestamp (outside tolerance) should fail."""
        future_timestamp = str(int(time.time()) + 120)  # 2 minutes ahead

        sig = signer._compute_signature("GET", "/api", b"", future_timestamp)

        with pytest.raises(SignatureVerificationError) as exc:
            signer.verify_or_raise(
                method="GET",
                url="/api",
                body=b"",
                signature=sig,
                timestamp=future_timestamp
            )

        assert "expired" in str(exc.value).lower() or "future" in str(exc.value).lower()


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_sign_request(self):
        """sign_request convenience function should work."""
        headers = sign_request(
            method="POST",
            url="/api/endpoint",
            body=b"data",
            secret="func_secret"
        )

        assert "X-Signature" in headers
        assert "X-Timestamp" in headers

    def test_verify_request_signature(self):
        """verify_request_signature convenience function should work."""
        headers = sign_request("GET", "/api", b"", "func_secret")

        result = verify_request_signature(
            method="GET",
            url="/api",
            body=b"",
            signature=headers["X-Signature"],
            timestamp=headers["X-Timestamp"],
            secret="func_secret"
        )

        assert result is True


class TestSignatureVerificationError:
    """Tests for SignatureVerificationError."""

    def test_error_message(self):
        """Error should include message."""
        error = SignatureVerificationError("Invalid signature")
        assert "Invalid signature" in str(error)

    def test_error_with_reason(self):
        """Error can include reason."""
        error = SignatureVerificationError("Failed", reason="timestamp_expired")
        assert error.reason == "timestamp_expired"


class TestEdgeCases:
    """Tests for edge cases."""

    @pytest.fixture
    def signer(self):
        return RequestSigner(secret="edge_secret")

    def test_empty_body(self, signer):
        """Empty body should be handled."""
        headers = signer.sign("GET", "/api", b"")

        result = signer.verify(
            method="GET",
            url="/api",
            body=b"",
            signature=headers["X-Signature"],
            timestamp=headers["X-Timestamp"]
        )

        assert result is True

    def test_large_body(self, signer):
        """Large body should be handled."""
        large_body = b"x" * 1000000  # 1MB

        headers = signer.sign("POST", "/api", large_body)

        result = signer.verify(
            method="POST",
            url="/api",
            body=large_body,
            signature=headers["X-Signature"],
            timestamp=headers["X-Timestamp"]
        )

        assert result is True

    def test_unicode_in_url(self, signer):
        """Unicode in URL should be handled."""
        url = "/api/search?q=日本語"

        headers = signer.sign("GET", url, b"")

        result = signer.verify(
            method="GET",
            url=url,
            body=b"",
            signature=headers["X-Signature"],
            timestamp=headers["X-Timestamp"]
        )

        assert result is True
