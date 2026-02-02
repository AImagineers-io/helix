"""
Integration tests for TLS Configuration (P12.5.3)

Tests TLS configuration including:
- TLS 1.2+ enforcement
- Strong cipher suites
- HSTS configuration
- Certificate validation helpers
"""
import pytest
import ssl

from core.tls_config import (
    TLSConfig,
    get_ssl_context,
    validate_certificate_file,
    get_recommended_ciphers,
    TLSConfigError,
    check_tls_version,
)


class TestTLSConfig:
    """Tests for TLS configuration."""

    def test_default_config(self):
        """Default config should enforce TLS 1.2+."""
        config = TLSConfig()
        assert config.minimum_version == "TLSv1.2"

    def test_custom_min_version(self):
        """Custom minimum version should be accepted."""
        config = TLSConfig(minimum_version="TLSv1.3")
        assert config.minimum_version == "TLSv1.3"

    def test_hsts_enabled_by_default(self):
        """HSTS should be enabled by default."""
        config = TLSConfig()
        assert config.hsts_enabled is True

    def test_hsts_max_age(self):
        """HSTS max age should be configurable."""
        config = TLSConfig(hsts_max_age=31536000)
        assert config.hsts_max_age == 31536000


class TestSSLContext:
    """Tests for SSL context creation."""

    def test_creates_ssl_context(self):
        """Should create SSL context."""
        config = TLSConfig()
        ctx = get_ssl_context(config)
        assert ctx is not None

    def test_enforces_minimum_version(self):
        """Should enforce minimum TLS version."""
        config = TLSConfig(minimum_version="TLSv1.2")
        ctx = get_ssl_context(config)

        # Should have TLS 1.2 as minimum
        assert ctx.minimum_version >= ssl.TLSVersion.TLSv1_2

    def test_disables_old_protocols(self):
        """Should disable SSLv2, SSLv3, TLSv1.0, TLSv1.1."""
        config = TLSConfig()
        ctx = get_ssl_context(config)

        # Old protocols should be disabled via minimum_version
        assert ctx.minimum_version >= ssl.TLSVersion.TLSv1_2


class TestCipherSuites:
    """Tests for cipher suite configuration."""

    def test_recommended_ciphers_list(self):
        """Should return list of recommended ciphers."""
        ciphers = get_recommended_ciphers()
        assert isinstance(ciphers, list)
        assert len(ciphers) > 0

    def test_excludes_weak_ciphers(self):
        """Should exclude weak ciphers."""
        ciphers = get_recommended_ciphers()
        cipher_str = ":".join(ciphers)

        # Should not include known weak ciphers
        assert "RC4" not in cipher_str
        assert "DES" not in cipher_str
        assert "MD5" not in cipher_str
        assert "NULL" not in cipher_str

    def test_includes_strong_ciphers(self):
        """Should include strong ciphers."""
        ciphers = get_recommended_ciphers()
        cipher_str = ":".join(ciphers)

        # Should include modern ciphers
        assert "AES" in cipher_str or "CHACHA20" in cipher_str


class TestCertificateValidation:
    """Tests for certificate validation."""

    def test_validates_pem_format(self, tmp_path):
        """Should validate PEM certificate format."""
        # Create a mock PEM file (not a real cert, just format check)
        cert_content = """-----BEGIN CERTIFICATE-----
MIIBkTCB+wIJAKHBfpG+/EvAMA0GCSqGSIb3DQEBCwUAMBExDzANBgNVBAMMBnVu
dXNlZDAeFw0yMDAxMDEwMDAwMDBaFw0zMDAxMDEwMDAwMDBaMBExDzANBgNVBAMM
BnVudXNlZDBcMA0GCSqGSIb3DQEBAQUAA0sAMEgCQQC5YrXV9ufmKxXO/RBxvYLH
tCGBkGBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBAgMB
AAEwDQYJKoZIhvcNAQELBQADQQAZCZMf1pOwvhIBBBBBBBBBBBBBBBBBBBBBBBBB
BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB=
-----END CERTIFICATE-----"""
        cert_file = tmp_path / "cert.pem"
        cert_file.write_text(cert_content)

        result = validate_certificate_file(str(cert_file))
        assert result.is_valid_format is True

    def test_rejects_invalid_format(self, tmp_path):
        """Should reject non-PEM format."""
        cert_file = tmp_path / "invalid.txt"
        cert_file.write_text("This is not a certificate")

        result = validate_certificate_file(str(cert_file))
        assert result.is_valid_format is False

    def test_rejects_missing_file(self):
        """Should reject missing file."""
        result = validate_certificate_file("/nonexistent/cert.pem")
        assert result.is_valid_format is False
        assert result.error is not None


class TestTLSVersionCheck:
    """Tests for TLS version checking."""

    def test_tls12_passes(self):
        """TLS 1.2 should pass minimum check."""
        result = check_tls_version("TLSv1.2", min_version="TLSv1.2")
        assert result is True

    def test_tls13_passes(self):
        """TLS 1.3 should pass minimum check."""
        result = check_tls_version("TLSv1.3", min_version="TLSv1.2")
        assert result is True

    def test_tls11_fails(self):
        """TLS 1.1 should fail minimum check."""
        result = check_tls_version("TLSv1.1", min_version="TLSv1.2")
        assert result is False

    def test_tls10_fails(self):
        """TLS 1.0 should fail minimum check."""
        result = check_tls_version("TLSv1.0", min_version="TLSv1.2")
        assert result is False


class TestTLSConfigError:
    """Tests for TLSConfigError."""

    def test_error_message(self):
        """Error should include message."""
        error = TLSConfigError("Invalid TLS configuration")
        assert "Invalid TLS configuration" in str(error)


class TestHSTSConfiguration:
    """Tests for HSTS configuration."""

    def test_hsts_header_value(self):
        """Should generate correct HSTS header."""
        config = TLSConfig(
            hsts_enabled=True,
            hsts_max_age=31536000,
            hsts_include_subdomains=True
        )

        header = config.get_hsts_header()
        assert "max-age=31536000" in header
        assert "includeSubDomains" in header

    def test_hsts_preload(self):
        """HSTS preload should be configurable."""
        config = TLSConfig(
            hsts_enabled=True,
            hsts_max_age=31536000,
            hsts_preload=True
        )

        header = config.get_hsts_header()
        assert "preload" in header

    def test_hsts_disabled(self):
        """Disabled HSTS should return empty."""
        config = TLSConfig(hsts_enabled=False)
        header = config.get_hsts_header()
        assert header == ""
