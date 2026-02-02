"""
Unit tests for URL Validation (P12.2.4)

Tests URL validation including:
- SSRF prevention
- Private IP blocking
- Protocol restriction (HTTPS only)
"""
import pytest

from core.validators import (
    URLValidator,
    URLValidationError,
    is_safe_url,
    is_private_ip,
    is_valid_protocol,
)


class TestPrivateIPDetection:
    """Tests for private IP detection."""

    def test_localhost_detected(self):
        """localhost should be detected as private."""
        assert is_private_ip("127.0.0.1") is True
        assert is_private_ip("127.0.0.100") is True
        assert is_private_ip("localhost") is True

    def test_private_class_a_detected(self):
        """10.x.x.x should be detected as private."""
        assert is_private_ip("10.0.0.1") is True
        assert is_private_ip("10.255.255.255") is True

    def test_private_class_b_detected(self):
        """172.16-31.x.x should be detected as private."""
        assert is_private_ip("172.16.0.1") is True
        assert is_private_ip("172.31.255.255") is True

    def test_private_class_c_detected(self):
        """192.168.x.x should be detected as private."""
        assert is_private_ip("192.168.0.1") is True
        assert is_private_ip("192.168.255.255") is True

    def test_public_ip_allowed(self):
        """Public IPs should be allowed."""
        assert is_private_ip("8.8.8.8") is False
        assert is_private_ip("1.1.1.1") is False
        assert is_private_ip("142.250.185.206") is False

    def test_link_local_detected(self):
        """Link-local addresses should be detected."""
        assert is_private_ip("169.254.0.1") is True
        assert is_private_ip("169.254.255.255") is True

    def test_ipv6_localhost_detected(self):
        """IPv6 localhost should be detected."""
        assert is_private_ip("::1") is True

    def test_metadata_ip_detected(self):
        """Cloud metadata IPs should be detected."""
        # AWS/Azure/GCP metadata endpoint
        assert is_private_ip("169.254.169.254") is True


class TestProtocolValidation:
    """Tests for protocol validation."""

    def test_https_allowed(self):
        """HTTPS should be allowed."""
        assert is_valid_protocol("https://example.com") is True

    def test_http_rejected_by_default(self):
        """HTTP should be rejected by default."""
        assert is_valid_protocol("http://example.com") is False

    def test_http_allowed_when_configured(self):
        """HTTP should be allowed when explicitly configured."""
        assert is_valid_protocol("http://example.com", allow_http=True) is True

    def test_ftp_rejected(self):
        """FTP should be rejected."""
        assert is_valid_protocol("ftp://example.com") is False

    def test_file_rejected(self):
        """file:// should be rejected."""
        assert is_valid_protocol("file:///etc/passwd") is False

    def test_javascript_rejected(self):
        """javascript: should be rejected."""
        assert is_valid_protocol("javascript:alert(1)") is False

    def test_data_rejected(self):
        """data: URLs should be rejected."""
        assert is_valid_protocol("data:text/html,<h1>test</h1>") is False


class TestURLValidator:
    """Tests for URLValidator class."""

    @pytest.fixture
    def validator(self):
        """Create URL validator instance."""
        return URLValidator()

    def test_valid_https_url(self, validator):
        """Valid HTTPS URL should pass."""
        result = validator.validate("https://example.com/webhook")
        assert result.is_valid is True

    def test_private_ip_rejected(self, validator):
        """URLs with private IPs should be rejected."""
        result = validator.validate("https://192.168.1.1/api")
        assert result.is_valid is False
        assert "private" in result.error.lower()

    def test_localhost_rejected(self, validator):
        """localhost URLs should be rejected."""
        result = validator.validate("https://localhost/api")
        assert result.is_valid is False
        assert "private" in result.error.lower() or "localhost" in result.error.lower()

    def test_http_rejected(self, validator):
        """HTTP URLs should be rejected."""
        result = validator.validate("http://example.com/webhook")
        assert result.is_valid is False
        assert "https" in result.error.lower() or "protocol" in result.error.lower()

    def test_invalid_url_rejected(self, validator):
        """Invalid URLs should be rejected."""
        result = validator.validate("not-a-valid-url")
        assert result.is_valid is False

    def test_internal_hostname_rejected(self, validator):
        """Internal hostnames should be rejected."""
        result = validator.validate("https://internal-server/api")
        assert result.is_valid is False

    def test_dns_rebinding_protection(self, validator):
        """DNS rebinding patterns should be detected."""
        # Hostname that could resolve to private IP
        result = validator.validate("https://127.0.0.1.nip.io/api")
        assert result.is_valid is False


class TestSSRFPrevention:
    """Tests for SSRF attack prevention."""

    @pytest.fixture
    def validator(self):
        return URLValidator()

    def test_aws_metadata_blocked(self, validator):
        """AWS metadata endpoint should be blocked."""
        result = validator.validate("https://169.254.169.254/latest/meta-data/")
        assert result.is_valid is False

    def test_gcp_metadata_blocked(self, validator):
        """GCP metadata endpoint should be blocked."""
        result = validator.validate("https://metadata.google.internal/")
        assert result.is_valid is False

    def test_azure_metadata_blocked(self, validator):
        """Azure metadata endpoint should be blocked."""
        result = validator.validate("https://169.254.169.254/metadata/instance")
        assert result.is_valid is False

    def test_encoded_ip_blocked(self, validator):
        """URL-encoded IPs should still be blocked."""
        # %31%32%37%2E%30%2E%30%2E%31 = 127.0.0.1
        result = validator.validate("https://%31%32%37%2E%30%2E%30%2E%31/api")
        assert result.is_valid is False

    def test_decimal_ip_blocked(self, validator):
        """Decimal IP notation should be blocked."""
        # 2130706433 = 127.0.0.1
        result = validator.validate("https://2130706433/api")
        assert result.is_valid is False


class TestIsSafeURL:
    """Tests for is_safe_url convenience function."""

    def test_safe_url_returns_true(self):
        """Safe URLs should return True."""
        assert is_safe_url("https://api.example.com/webhook") is True

    def test_unsafe_url_returns_false(self):
        """Unsafe URLs should return False."""
        assert is_safe_url("http://localhost/admin") is False
        assert is_safe_url("https://192.168.1.1/api") is False
