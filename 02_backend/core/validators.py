"""
URL Validation for SSRF prevention and webhook security.

Provides:
- Private IP detection and blocking
- Protocol restriction (HTTPS only by default)
- SSRF attack prevention
- Internal hostname blocking

Used for:
- Webhook URL validation
- External API endpoint validation
- User-provided URL verification
"""
import ipaddress
import re
import socket
from dataclasses import dataclass
from typing import Optional
from urllib.parse import urlparse, unquote

# Internal/private hostname patterns to block
INTERNAL_HOSTNAME_PATTERNS = [
    r"^localhost$",
    r"^.*\.local$",
    r"^.*\.internal$",
    r"^.*\.localdomain$",
    r"^.*\.corp$",
    r"^metadata\.google\.internal$",
    r"^.*\.amazonaws\.com$",  # AWS internal
]

# Cloud metadata IP addresses
METADATA_IPS = {"169.254.169.254"}


class URLValidationError(Exception):
    """Raised when URL validation fails."""
    pass


@dataclass
class URLValidationResult:
    """Result of URL validation."""
    is_valid: bool
    error: str = ""
    normalized_url: Optional[str] = None


def is_private_ip(host: str) -> bool:
    """
    Check if a host is a private/internal IP address.

    Detects:
    - localhost (127.0.0.0/8)
    - Private networks (10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16)
    - Link-local (169.254.0.0/16)
    - Cloud metadata endpoints (169.254.169.254)
    - IPv6 localhost (::1)

    Args:
        host: Hostname or IP address

    Returns:
        bool: True if host is private/internal
    """
    # Handle localhost string
    if host.lower() == "localhost":
        return True

    # Check metadata IPs
    if host in METADATA_IPS:
        return True

    # Try to parse as IP address
    try:
        ip = ipaddress.ip_address(host)

        # IPv6 localhost
        if ip == ipaddress.ip_address("::1"):
            return True

        # IPv4 private/reserved
        if isinstance(ip, ipaddress.IPv4Address):
            return (
                ip.is_private
                or ip.is_loopback
                or ip.is_link_local
                or ip.is_reserved
            )

        # IPv6 private
        if isinstance(ip, ipaddress.IPv6Address):
            return (
                ip.is_private
                or ip.is_loopback
                or ip.is_link_local
                or ip.is_reserved
            )

    except ValueError:
        # Not a valid IP - check for special hostnames
        pass

    # Check for decimal IP notation (e.g., 2130706433 = 127.0.0.1)
    try:
        decimal_ip = int(host)
        if 0 <= decimal_ip <= 0xFFFFFFFF:
            ip_str = socket.inet_ntoa(decimal_ip.to_bytes(4, byteorder="big"))
            return is_private_ip(ip_str)
    except (ValueError, OverflowError):
        pass

    return False


def is_valid_protocol(url: str, allow_http: bool = False) -> bool:
    """
    Check if URL uses an allowed protocol.

    Args:
        url: URL to check
        allow_http: Whether to allow HTTP (default: HTTPS only)

    Returns:
        bool: True if protocol is allowed
    """
    allowed = {"https"}
    if allow_http:
        allowed.add("http")

    try:
        parsed = urlparse(url)
        return parsed.scheme.lower() in allowed
    except Exception:
        return False


def _is_internal_hostname(hostname: str) -> bool:
    """Check if hostname matches internal patterns."""
    hostname_lower = hostname.lower()

    for pattern in INTERNAL_HOSTNAME_PATTERNS:
        if re.match(pattern, hostname_lower):
            return True

    # Check for single-word hostnames (likely internal)
    if "." not in hostname and hostname != "localhost":
        return True

    return False


def _decode_url(url: str) -> str:
    """Decode URL-encoded characters."""
    decoded = url
    # Multiple rounds to handle double-encoding
    for _ in range(3):
        new_decoded = unquote(decoded)
        if new_decoded == decoded:
            break
        decoded = new_decoded
    return decoded


class URLValidator:
    """
    Validates URLs for security concerns.

    Checks:
    1. Protocol is HTTPS (configurable)
    2. Host is not a private IP
    3. Host is not an internal hostname
    4. URL is well-formed

    Prevents SSRF attacks by blocking:
    - Private IPs
    - localhost
    - Internal hostnames
    - Cloud metadata endpoints
    """

    def __init__(self, allow_http: bool = False):
        """
        Initialize URL validator.

        Args:
            allow_http: Whether to allow HTTP (default: HTTPS only)
        """
        self.allow_http = allow_http

    def validate(self, url: str) -> URLValidationResult:
        """
        Validate a URL for security.

        Args:
            url: URL to validate

        Returns:
            URLValidationResult: Validation result
        """
        if not url:
            return URLValidationResult(
                is_valid=False,
                error="URL is empty"
            )

        # Decode URL to catch encoding tricks
        decoded_url = _decode_url(url)

        # Parse URL
        try:
            parsed = urlparse(decoded_url)
        except Exception:
            return URLValidationResult(
                is_valid=False,
                error="Invalid URL format"
            )

        # Check protocol
        if not is_valid_protocol(decoded_url, self.allow_http):
            return URLValidationResult(
                is_valid=False,
                error="Only HTTPS protocol is allowed"
            )

        # Get hostname
        hostname = parsed.hostname
        if not hostname:
            return URLValidationResult(
                is_valid=False,
                error="URL must have a hostname"
            )

        # Check for private IP
        if is_private_ip(hostname):
            return URLValidationResult(
                is_valid=False,
                error="Private/internal IP addresses are not allowed"
            )

        # Check for internal hostname patterns
        if _is_internal_hostname(hostname):
            return URLValidationResult(
                is_valid=False,
                error="Internal hostnames are not allowed"
            )

        # Check for IP-like patterns in hostname (nip.io, xip.io, etc.)
        ip_pattern = r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}"
        if re.search(ip_pattern, hostname):
            # Extract and check the IP
            match = re.search(ip_pattern, hostname)
            if match and is_private_ip(match.group()):
                return URLValidationResult(
                    is_valid=False,
                    error="URLs containing private IPs are not allowed"
                )

        return URLValidationResult(
            is_valid=True,
            normalized_url=decoded_url
        )


def is_safe_url(url: str) -> bool:
    """
    Convenience function to check if a URL is safe.

    Args:
        url: URL to check

    Returns:
        bool: True if URL passes all security checks
    """
    validator = URLValidator()
    result = validator.validate(url)
    return result.is_valid
