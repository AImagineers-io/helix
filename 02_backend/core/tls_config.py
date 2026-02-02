"""
TLS Configuration for secure connections.

Provides:
- TLS 1.2+ enforcement
- Strong cipher suites
- HSTS configuration
- Certificate validation helpers

Requirements:
- TLS 1.2 minimum
- Strong cipher suites only
- HSTS enabled with long max-age
"""
import ssl
import os
from dataclasses import dataclass
from typing import Optional


class TLSConfigError(Exception):
    """Error in TLS configuration."""
    pass


@dataclass
class CertificateValidationResult:
    """Result of certificate validation."""
    is_valid_format: bool
    error: Optional[str] = None
    expires: Optional[str] = None
    subject: Optional[str] = None


@dataclass
class TLSConfig:
    """Configuration for TLS."""
    minimum_version: str = "TLSv1.2"
    hsts_enabled: bool = True
    hsts_max_age: int = 31536000  # 1 year
    hsts_include_subdomains: bool = True
    hsts_preload: bool = False
    verify_certificates: bool = True
    cert_file: Optional[str] = None
    key_file: Optional[str] = None

    def get_hsts_header(self) -> str:
        """
        Generate HSTS header value.

        Returns:
            str: HSTS header value or empty string if disabled
        """
        if not self.hsts_enabled:
            return ""

        parts = [f"max-age={self.hsts_max_age}"]

        if self.hsts_include_subdomains:
            parts.append("includeSubDomains")

        if self.hsts_preload:
            parts.append("preload")

        return "; ".join(parts)


# Recommended cipher suites (modern, secure)
RECOMMENDED_CIPHERS = [
    # TLS 1.3 ciphers (if available)
    "TLS_AES_256_GCM_SHA384",
    "TLS_CHACHA20_POLY1305_SHA256",
    "TLS_AES_128_GCM_SHA256",
    # TLS 1.2 ciphers
    "ECDHE-ECDSA-AES256-GCM-SHA384",
    "ECDHE-RSA-AES256-GCM-SHA384",
    "ECDHE-ECDSA-CHACHA20-POLY1305",
    "ECDHE-RSA-CHACHA20-POLY1305",
    "ECDHE-ECDSA-AES128-GCM-SHA256",
    "ECDHE-RSA-AES128-GCM-SHA256",
    "DHE-RSA-AES256-GCM-SHA384",
    "DHE-RSA-AES128-GCM-SHA256",
]


def get_recommended_ciphers() -> list[str]:
    """
    Get list of recommended cipher suites.

    Returns:
        list[str]: Cipher suite names
    """
    return RECOMMENDED_CIPHERS.copy()


def _version_to_ssl(version: str) -> ssl.TLSVersion:
    """
    Convert version string to ssl.TLSVersion.

    Args:
        version: Version string like "TLSv1.2"

    Returns:
        ssl.TLSVersion: SSL version enum
    """
    mapping = {
        "TLSv1.0": ssl.TLSVersion.TLSv1,
        "TLSv1.1": ssl.TLSVersion.TLSv1_1,
        "TLSv1.2": ssl.TLSVersion.TLSv1_2,
        "TLSv1.3": ssl.TLSVersion.TLSv1_3,
    }
    return mapping.get(version, ssl.TLSVersion.TLSv1_2)


def get_ssl_context(config: TLSConfig) -> ssl.SSLContext:
    """
    Create SSL context with secure configuration.

    Args:
        config: TLS configuration

    Returns:
        ssl.SSLContext: Configured SSL context
    """
    # Create context with TLS client purpose
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)

    # Set minimum version
    ctx.minimum_version = _version_to_ssl(config.minimum_version)

    # Disable old protocols explicitly
    ctx.options |= ssl.OP_NO_SSLv2
    ctx.options |= ssl.OP_NO_SSLv3

    # Set cipher suites
    try:
        cipher_string = ":".join(RECOMMENDED_CIPHERS)
        ctx.set_ciphers(cipher_string)
    except ssl.SSLError:
        # Fall back to HIGH ciphers if specific ones aren't available
        ctx.set_ciphers("HIGH:!aNULL:!MD5:!RC4")

    # Certificate verification
    if config.verify_certificates:
        ctx.verify_mode = ssl.CERT_REQUIRED
        ctx.check_hostname = True
        ctx.load_default_certs()
    else:
        ctx.verify_mode = ssl.CERT_NONE
        ctx.check_hostname = False

    # Load certificate and key if provided
    if config.cert_file and config.key_file:
        ctx.load_cert_chain(config.cert_file, config.key_file)

    return ctx


def validate_certificate_file(path: str) -> CertificateValidationResult:
    """
    Validate certificate file format.

    Args:
        path: Path to certificate file

    Returns:
        CertificateValidationResult: Validation result
    """
    if not os.path.exists(path):
        return CertificateValidationResult(
            is_valid_format=False,
            error=f"File not found: {path}"
        )

    try:
        with open(path, "r") as f:
            content = f.read()

        # Basic PEM format check
        if "-----BEGIN CERTIFICATE-----" not in content:
            return CertificateValidationResult(
                is_valid_format=False,
                error="Not a PEM certificate file"
            )

        if "-----END CERTIFICATE-----" not in content:
            return CertificateValidationResult(
                is_valid_format=False,
                error="Incomplete PEM certificate"
            )

        return CertificateValidationResult(is_valid_format=True)

    except Exception as e:
        return CertificateValidationResult(
            is_valid_format=False,
            error=str(e)
        )


def check_tls_version(
    version: str,
    min_version: str = "TLSv1.2"
) -> bool:
    """
    Check if TLS version meets minimum requirement.

    Args:
        version: Version to check (e.g., "TLSv1.2")
        min_version: Minimum required version

    Returns:
        bool: True if version meets requirement
    """
    version_order = ["SSLv2", "SSLv3", "TLSv1.0", "TLSv1.1", "TLSv1.2", "TLSv1.3"]

    try:
        version_idx = version_order.index(version)
        min_idx = version_order.index(min_version)
        return version_idx >= min_idx
    except ValueError:
        return False
