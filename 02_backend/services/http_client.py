"""
HTTP Client with Request Signing for internal API calls.

Provides:
- HMAC signature for outbound requests
- Timestamp validation
- Replay attack prevention
- Signature verification

Use for internal service-to-service communication.
"""
import hmac
import hashlib
import time
from dataclasses import dataclass
from typing import Optional


# Default timestamp tolerance (5 minutes)
DEFAULT_TIMESTAMP_TOLERANCE = 300


@dataclass
class SignatureConfig:
    """Configuration for request signing."""
    timestamp_tolerance_seconds: int = DEFAULT_TIMESTAMP_TOLERANCE
    algorithm: str = "sha256"


class SignatureVerificationError(Exception):
    """Error raised when signature verification fails."""

    def __init__(self, message: str, reason: Optional[str] = None):
        """
        Initialize verification error.

        Args:
            message: Error message
            reason: Specific failure reason
        """
        super().__init__(message)
        self.reason = reason


class RequestSigner:
    """
    Signs and verifies HTTP request signatures.

    Uses HMAC-SHA256 to sign request method, URL, body, and timestamp.
    Prevents replay attacks by validating timestamp freshness.
    """

    def __init__(
        self,
        secret: str,
        config: Optional[SignatureConfig] = None
    ):
        """
        Initialize request signer.

        Args:
            secret: Shared secret for HMAC
            config: Signature configuration
        """
        self.secret = secret
        self.config = config or SignatureConfig()

    def sign(
        self,
        method: str,
        url: str,
        body: bytes
    ) -> dict[str, str]:
        """
        Sign an HTTP request.

        Args:
            method: HTTP method (GET, POST, etc.)
            url: Request URL path
            body: Request body bytes

        Returns:
            dict: Headers to include in request
        """
        timestamp = str(int(time.time()))
        signature = self._compute_signature(method, url, body, timestamp)

        return {
            "X-Signature": signature,
            "X-Timestamp": timestamp,
        }

    def verify(
        self,
        method: str,
        url: str,
        body: bytes,
        signature: str,
        timestamp: str
    ) -> bool:
        """
        Verify request signature.

        Args:
            method: HTTP method
            url: Request URL path
            body: Request body bytes
            signature: X-Signature header value
            timestamp: X-Timestamp header value

        Returns:
            bool: True if signature is valid
        """
        try:
            self.verify_or_raise(method, url, body, signature, timestamp)
            return True
        except SignatureVerificationError:
            return False

    def verify_or_raise(
        self,
        method: str,
        url: str,
        body: bytes,
        signature: str,
        timestamp: str
    ) -> None:
        """
        Verify request signature, raising on failure.

        Args:
            method: HTTP method
            url: Request URL path
            body: Request body bytes
            signature: X-Signature header value
            timestamp: X-Timestamp header value

        Raises:
            SignatureVerificationError: If verification fails
        """
        # Validate timestamp
        try:
            ts = int(timestamp)
        except (ValueError, TypeError):
            raise SignatureVerificationError(
                "Invalid timestamp format",
                reason="invalid_timestamp"
            )

        now = int(time.time())
        age = abs(now - ts)

        if age > self.config.timestamp_tolerance_seconds:
            raise SignatureVerificationError(
                f"Timestamp expired (age: {age}s, tolerance: {self.config.timestamp_tolerance_seconds}s)",
                reason="timestamp_expired"
            )

        # Verify signature
        expected = self._compute_signature(method, url, body, timestamp)

        if not hmac.compare_digest(signature, expected):
            raise SignatureVerificationError(
                "Signature mismatch",
                reason="invalid_signature"
            )

    def _compute_signature(
        self,
        method: str,
        url: str,
        body: bytes,
        timestamp: str
    ) -> str:
        """
        Compute HMAC signature for request.

        Args:
            method: HTTP method
            url: Request URL
            body: Request body
            timestamp: Unix timestamp string

        Returns:
            str: Hex-encoded HMAC signature
        """
        # Build signing string
        signing_string = f"{method.upper()}\n{url}\n{timestamp}\n"
        signing_bytes = signing_string.encode("utf-8") + body

        # Compute HMAC
        sig = hmac.new(
            self.secret.encode("utf-8"),
            signing_bytes,
            hashlib.sha256
        ).hexdigest()

        return sig


def sign_request(
    method: str,
    url: str,
    body: bytes,
    secret: str
) -> dict[str, str]:
    """
    Convenience function to sign a request.

    Args:
        method: HTTP method
        url: Request URL
        body: Request body
        secret: Shared secret

    Returns:
        dict: Headers to include
    """
    signer = RequestSigner(secret)
    return signer.sign(method, url, body)


def verify_request_signature(
    method: str,
    url: str,
    body: bytes,
    signature: str,
    timestamp: str,
    secret: str
) -> bool:
    """
    Convenience function to verify request signature.

    Args:
        method: HTTP method
        url: Request URL
        body: Request body
        signature: X-Signature header
        timestamp: X-Timestamp header
        secret: Shared secret

    Returns:
        bool: True if valid
    """
    signer = RequestSigner(secret)
    return signer.verify(method, url, body, signature, timestamp)
