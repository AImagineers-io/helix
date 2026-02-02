"""
Webhook Security for signature validation.

Provides:
- HMAC signature computation
- Facebook X-Hub-Signature-256 validation
- Timing-safe comparison
- Multi-provider support

All webhook payloads should be validated before processing.
"""
import hmac
import hashlib
import secrets
from typing import Optional


class WebhookValidationError(Exception):
    """Error raised when webhook validation fails."""

    def __init__(self, message: str, provider: Optional[str] = None):
        """
        Initialize validation error.

        Args:
            message: Error message
            provider: Webhook provider name
        """
        super().__init__(message)
        self.provider = provider


def timing_safe_compare(a: str, b: str) -> bool:
    """
    Compare two strings in constant time.

    This prevents timing attacks that could leak
    information about the expected signature.

    Args:
        a: First string
        b: Second string

    Returns:
        bool: True if strings match
    """
    return secrets.compare_digest(a, b)


def compute_signature(payload: bytes, secret: str) -> str:
    """
    Compute HMAC-SHA256 signature for payload.

    Args:
        payload: Raw request body bytes
        secret: Webhook secret key

    Returns:
        str: Signature with sha256= prefix
    """
    sig = hmac.new(
        secret.encode("utf-8"),
        payload,
        hashlib.sha256
    ).hexdigest()

    return f"sha256={sig}"


def validate_facebook_signature(
    payload: bytes,
    signature: Optional[str],
    secret: str
) -> bool:
    """
    Validate Facebook webhook signature.

    Facebook sends X-Hub-Signature-256 header with format:
    sha256=<hex_signature>

    Args:
        payload: Raw request body bytes
        signature: X-Hub-Signature-256 header value
        secret: Facebook App Secret

    Returns:
        bool: True if signature is valid
    """
    if not signature:
        return False

    # Signature must start with sha256=
    if not signature.startswith("sha256="):
        return False

    expected = compute_signature(payload, secret)

    # Use timing-safe comparison
    return timing_safe_compare(signature.lower(), expected.lower())


class WebhookSignatureValidator:
    """
    Multi-provider webhook signature validator.

    Supports validating signatures from different webhook
    providers (Facebook, Stripe, GitHub, etc.).
    """

    def __init__(self, secrets: Optional[dict[str, str]] = None):
        """
        Initialize validator with provider secrets.

        Args:
            secrets: Dict mapping provider name to secret
        """
        self._secrets: dict[str, str] = secrets or {}

    def add_provider(self, provider: str, secret: str) -> None:
        """
        Add or update a provider secret.

        Args:
            provider: Provider name (e.g., "facebook", "stripe")
            secret: Webhook secret for this provider
        """
        self._secrets[provider] = secret

    def validate(
        self,
        provider: str,
        payload: bytes,
        signature: str
    ) -> bool:
        """
        Validate webhook signature for provider.

        Args:
            provider: Provider name
            payload: Raw request body bytes
            signature: Signature header value

        Returns:
            bool: True if signature is valid

        Raises:
            WebhookValidationError: If provider is unknown
        """
        if provider not in self._secrets:
            raise WebhookValidationError(
                f"Unknown provider: {provider}",
                provider=provider
            )

        secret = self._secrets[provider]

        # Normalize signature
        normalized_sig = self._normalize_signature(signature)
        expected = compute_signature(payload, secret)

        return timing_safe_compare(normalized_sig.lower(), expected.lower())

    def _normalize_signature(self, signature: str) -> str:
        """
        Normalize signature to sha256=<hex> format.

        Args:
            signature: Raw signature string

        Returns:
            str: Normalized signature
        """
        if not signature:
            return ""

        # Already has prefix
        if signature.lower().startswith("sha256="):
            return signature

        # Assume raw hex, add prefix
        return f"sha256={signature}"
