"""
API Key Service for key generation, rotation, and revocation.

Provides:
- Secure API key generation with 'hx_' prefix
- Key hashing for storage (SHA-256)
- Key rotation with configurable grace period (default 24h)
- Key revocation and lifecycle management

Example:
    service = APIKeyService()
    key = service.create_api_key(name="Production")
    print(f"New key: {key.raw_key}")  # Only available at creation

    # Later, rotate the key
    rotated = service.rotate_api_key(key.id)
    # Old key valid for 24 hours, new key immediately valid
"""
import hashlib
import hmac
import secrets
from dataclasses import dataclass, replace
from datetime import datetime, timedelta
from typing import Optional

# API Key configuration
API_KEY_PREFIX = "hx_"
API_KEY_LENGTH = 16  # bytes, produces 32 hex chars
DEFAULT_GRACE_PERIOD_HOURS = 24


class APIKeyRotationError(Exception):
    """Raised when API key rotation or revocation fails."""
    pass


@dataclass
class APIKey:
    """
    Represents an API key with metadata.

    Attributes:
        id: Unique identifier for the key
        name: Human-readable name
        key_hash: SHA-256 hash of the key (for storage)
        created_at: When the key was created
        raw_key: The actual key value (only at creation/rotation)
        previous_key_hash: Hash of previous key during grace period
        previous_key_expires_at: When grace period ends
        revoked_at: When key was revoked (None if active)
        last_used_at: Last validation timestamp
    """
    id: str
    name: str
    key_hash: str
    created_at: datetime
    raw_key: Optional[str] = None
    previous_key_hash: Optional[str] = None
    previous_key_expires_at: Optional[datetime] = None
    revoked_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None

    @property
    def is_active(self) -> bool:
        """Check if key is active (not revoked)."""
        return self.revoked_at is None

    @property
    def is_in_grace_period(self) -> bool:
        """Check if key has a previous key in grace period."""
        if self.previous_key_expires_at is None:
            return False
        return datetime.utcnow() < self.previous_key_expires_at


def generate_api_key() -> str:
    """
    Generate a cryptographically secure API key.

    Uses secrets.token_hex for cryptographically strong random generation.

    Returns:
        str: API key in format 'hx_<32 hex chars>'
    """
    key_body = secrets.token_hex(API_KEY_LENGTH)
    return f"{API_KEY_PREFIX}{key_body}"


def hash_api_key(key: str) -> str:
    """
    Hash an API key for secure storage.

    Uses SHA-256 which is deterministic (same key = same hash).
    This allows for key lookup without storing the raw key.

    Args:
        key: Raw API key

    Returns:
        str: Hashed key (hex-encoded SHA-256)
    """
    return hashlib.sha256(key.encode()).hexdigest()


def verify_api_key(key: str, key_hash: str) -> bool:
    """
    Verify an API key against its stored hash.

    Uses timing-safe comparison to prevent timing attacks.

    Args:
        key: Raw API key to verify
        key_hash: Stored hash to compare against

    Returns:
        bool: True if key matches hash
    """
    if not key:
        return False
    computed_hash = hash_api_key(key)
    return hmac.compare_digest(computed_hash, key_hash)


class APIKeyService:
    """
    Service for managing API keys with rotation support.

    Provides secure key lifecycle management including:
    - Key creation with secure random generation
    - Key rotation with configurable grace period
    - Key revocation
    - Key validation (current and previous during grace)

    Attributes:
        grace_period_hours: Hours old key remains valid after rotation
    """

    def __init__(self, grace_period_hours: int = DEFAULT_GRACE_PERIOD_HOURS):
        """
        Initialize API key service.

        Args:
            grace_period_hours: Hours old key remains valid after rotation.
                               Default is 24 hours for dual-key support.
        """
        self.grace_period_hours = grace_period_hours
        self._keys: dict[str, APIKey] = {}

    def _get_current_time(self) -> datetime:
        """Get current UTC time. Extracted for testing."""
        return datetime.utcnow()

    def _generate_key_id(self) -> str:
        """Generate unique key ID using secure random."""
        return secrets.token_hex(8)

    def create_api_key(self, name: str) -> APIKey:
        """
        Create a new API key.

        The returned APIKey contains raw_key which should be shown
        to the user once and never stored. Only the hash is persisted.

        Args:
            name: Human-readable name for the key

        Returns:
            APIKey: Key object with raw_key populated (one-time access)
        """
        raw_key = generate_api_key()
        key_hash = hash_api_key(raw_key)
        key_id = self._generate_key_id()

        api_key = APIKey(
            id=key_id,
            name=name,
            key_hash=key_hash,
            created_at=self._get_current_time(),
            raw_key=raw_key,
        )

        self._keys[key_id] = api_key
        return api_key

    def get_api_key(self, key_id: str) -> Optional[APIKey]:
        """
        Get API key by ID.

        Args:
            key_id: Key identifier

        Returns:
            APIKey or None if not found
        """
        return self._keys.get(key_id)

    def validate_api_key(self, raw_key: str) -> bool:
        """
        Validate a raw API key.

        Checks:
        1. Current active keys
        2. Previous keys during their grace period

        This allows seamless key rotation without service disruption.

        Args:
            raw_key: Raw API key to validate

        Returns:
            bool: True if key is valid and active
        """
        if not raw_key:
            return False

        key_hash = hash_api_key(raw_key)
        current_time = self._get_current_time()

        for api_key in self._keys.values():
            if not api_key.is_active:
                continue

            # Check current key (timing-safe)
            if hmac.compare_digest(api_key.key_hash, key_hash):
                return True

            # Check previous key during grace period
            if self._is_valid_grace_period_key(api_key, key_hash, current_time):
                return True

        return False

    def _is_valid_grace_period_key(
        self,
        api_key: APIKey,
        key_hash: str,
        current_time: datetime
    ) -> bool:
        """Check if key_hash matches a previous key within grace period."""
        if api_key.previous_key_hash is None:
            return False
        if api_key.previous_key_expires_at is None:
            return False
        if current_time >= api_key.previous_key_expires_at:
            return False
        return hmac.compare_digest(api_key.previous_key_hash, key_hash)

    def rotate_api_key(self, key_id: str) -> APIKey:
        """
        Rotate an API key, maintaining old key during grace period.

        The old key remains valid for grace_period_hours, allowing
        clients time to update to the new key without service disruption.

        Args:
            key_id: ID of key to rotate

        Returns:
            APIKey: Updated key with new raw_key

        Raises:
            APIKeyRotationError: If key not found
        """
        api_key = self._keys.get(key_id)
        if api_key is None:
            raise APIKeyRotationError("API key not found")

        # Generate new key
        new_raw_key = generate_api_key()
        new_key_hash = hash_api_key(new_raw_key)

        # Calculate grace period end
        current_time = self._get_current_time()
        grace_period_end = current_time + timedelta(hours=self.grace_period_hours)

        # Update key: store old hash for grace period, set new key
        api_key.previous_key_hash = api_key.key_hash
        api_key.previous_key_expires_at = grace_period_end
        api_key.key_hash = new_key_hash
        api_key.raw_key = new_raw_key

        return api_key

    def revoke_api_key(self, key_id: str) -> None:
        """
        Revoke an API key immediately.

        Revocation is immediate - the key and any grace period key
        become invalid instantly.

        Args:
            key_id: ID of key to revoke

        Raises:
            APIKeyRotationError: If key not found or already revoked
        """
        api_key = self._keys.get(key_id)
        if api_key is None:
            raise APIKeyRotationError("API key not found")

        if api_key.revoked_at is not None:
            raise APIKeyRotationError("API key already revoked")

        api_key.revoked_at = self._get_current_time()
        # Clear grace period on revocation for security
        api_key.previous_key_hash = None
        api_key.previous_key_expires_at = None

    def list_api_keys(self, include_revoked: bool = False) -> list[APIKey]:
        """
        List API keys.

        Returns copies without raw_key for security.

        Args:
            include_revoked: Whether to include revoked keys

        Returns:
            List of APIKey objects (raw_key always None)
        """
        keys = []
        for api_key in self._keys.values():
            if not include_revoked and not api_key.is_active:
                continue
            # Create copy without raw_key for security
            key_copy = replace(api_key, raw_key=None)
            keys.append(key_copy)
        return keys
