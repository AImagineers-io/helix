"""
Integration tests for API Key Rotation (P12.1.3)

Tests the API key rotation service including:
- Generate new API key
- Grace period with dual-key support (24h)
- Revoke old key
- Validation of both keys during grace period
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from services.api_key_service import (
    APIKeyService,
    APIKey,
    APIKeyRotationError,
    generate_api_key,
    hash_api_key,
    verify_api_key,
)


class TestAPIKeyGeneration:
    """Tests for API key generation."""

    def test_generate_api_key_returns_valid_format(self):
        """Generated API key should have correct prefix and length."""
        key = generate_api_key()
        assert key.startswith("hx_")
        assert len(key) == 35  # "hx_" + 32 chars

    def test_generate_api_key_unique(self):
        """Each generated key should be unique."""
        keys = [generate_api_key() for _ in range(100)]
        assert len(set(keys)) == 100

    def test_generate_api_key_cryptographically_secure(self):
        """Key should use secure random generation."""
        key = generate_api_key()
        # Key body (after prefix) should be hex characters
        key_body = key[3:]
        assert all(c in "0123456789abcdef" for c in key_body)


class TestAPIKeyHashing:
    """Tests for API key hashing and verification."""

    def test_hash_api_key_returns_different_value(self):
        """Hash should not equal original key."""
        key = "hx_abcdef1234567890abcdef1234567890"
        hashed = hash_api_key(key)
        assert hashed != key

    def test_hash_api_key_consistent(self):
        """Same key should produce same hash."""
        key = "hx_abcdef1234567890abcdef1234567890"
        hash1 = hash_api_key(key)
        hash2 = hash_api_key(key)
        assert hash1 == hash2

    def test_verify_api_key_correct(self):
        """Verification should succeed with correct key."""
        key = "hx_abcdef1234567890abcdef1234567890"
        hashed = hash_api_key(key)
        assert verify_api_key(key, hashed) is True

    def test_verify_api_key_incorrect(self):
        """Verification should fail with wrong key."""
        key1 = "hx_abcdef1234567890abcdef1234567890"
        key2 = "hx_00000000000000000000000000000000"
        hashed = hash_api_key(key1)
        assert verify_api_key(key2, hashed) is False

    def test_verify_api_key_empty(self):
        """Verification should handle empty key gracefully."""
        key = "hx_abcdef1234567890abcdef1234567890"
        hashed = hash_api_key(key)
        assert verify_api_key("", hashed) is False


class TestAPIKeyService:
    """Tests for API key service operations."""

    @pytest.fixture
    def api_key_service(self):
        """Create API key service instance."""
        return APIKeyService()

    def test_create_api_key_returns_key_object(self, api_key_service):
        """Creating key should return APIKey object with raw key."""
        result = api_key_service.create_api_key(name="Test Key")
        assert isinstance(result, APIKey)
        assert result.name == "Test Key"
        assert result.raw_key is not None
        assert result.raw_key.startswith("hx_")

    def test_create_api_key_stores_hash_not_raw(self, api_key_service):
        """Service should store hash, not raw key."""
        result = api_key_service.create_api_key(name="Test Key")
        # The key_hash should not equal the raw key
        assert result.key_hash != result.raw_key

    def test_validate_api_key_valid(self, api_key_service):
        """Valid API key should pass validation."""
        result = api_key_service.create_api_key(name="Test Key")
        is_valid = api_key_service.validate_api_key(result.raw_key)
        assert is_valid is True

    def test_validate_api_key_invalid(self, api_key_service):
        """Invalid API key should fail validation."""
        is_valid = api_key_service.validate_api_key("hx_invalid_key_12345678")
        assert is_valid is False


class TestAPIKeyRotation:
    """Tests for API key rotation with grace period."""

    @pytest.fixture
    def api_key_service(self):
        """Create API key service instance."""
        return APIKeyService()

    def test_rotate_api_key_returns_new_key(self, api_key_service):
        """Rotation should return a new API key."""
        original = api_key_service.create_api_key(name="Production Key")
        original_raw_key = original.raw_key  # Capture before mutation
        rotated = api_key_service.rotate_api_key(original.id)

        assert rotated.raw_key is not None
        assert rotated.raw_key != original_raw_key

    def test_rotate_api_key_old_key_valid_during_grace_period(self, api_key_service):
        """Old key should remain valid during 24h grace period."""
        original = api_key_service.create_api_key(name="Production Key")
        original_raw = original.raw_key

        api_key_service.rotate_api_key(original.id)

        # Old key should still work during grace period
        assert api_key_service.validate_api_key(original_raw) is True

    def test_rotate_api_key_new_key_valid_immediately(self, api_key_service):
        """New key should be valid immediately after rotation."""
        original = api_key_service.create_api_key(name="Production Key")
        rotated = api_key_service.rotate_api_key(original.id)

        assert api_key_service.validate_api_key(rotated.raw_key) is True

    def test_rotate_api_key_old_key_invalid_after_grace_period(self, api_key_service):
        """Old key should be invalid after grace period expires."""
        original = api_key_service.create_api_key(name="Production Key")
        original_raw = original.raw_key

        api_key_service.rotate_api_key(original.id)

        # Simulate time passing beyond grace period (24 hours)
        with patch.object(
            api_key_service, '_get_current_time',
            return_value=datetime.utcnow() + timedelta(hours=25)
        ):
            assert api_key_service.validate_api_key(original_raw) is False

    def test_rotate_nonexistent_key_raises_error(self, api_key_service):
        """Rotating non-existent key should raise error."""
        with pytest.raises(APIKeyRotationError, match="API key not found"):
            api_key_service.rotate_api_key("nonexistent-id")


class TestAPIKeyRevocation:
    """Tests for API key revocation."""

    @pytest.fixture
    def api_key_service(self):
        """Create API key service instance."""
        return APIKeyService()

    def test_revoke_api_key_invalidates_key(self, api_key_service):
        """Revoked key should no longer be valid."""
        key = api_key_service.create_api_key(name="Test Key")
        api_key_service.revoke_api_key(key.id)

        assert api_key_service.validate_api_key(key.raw_key) is False

    def test_revoke_api_key_sets_revoked_at(self, api_key_service):
        """Revoked key should have revoked_at timestamp."""
        key = api_key_service.create_api_key(name="Test Key")
        api_key_service.revoke_api_key(key.id)

        revoked_key = api_key_service.get_api_key(key.id)
        assert revoked_key.revoked_at is not None

    def test_revoke_nonexistent_key_raises_error(self, api_key_service):
        """Revoking non-existent key should raise error."""
        with pytest.raises(APIKeyRotationError, match="API key not found"):
            api_key_service.revoke_api_key("nonexistent-id")

    def test_revoke_already_revoked_key_raises_error(self, api_key_service):
        """Revoking already revoked key should raise error."""
        key = api_key_service.create_api_key(name="Test Key")
        api_key_service.revoke_api_key(key.id)

        with pytest.raises(APIKeyRotationError, match="already revoked"):
            api_key_service.revoke_api_key(key.id)


class TestAPIKeyGracePeriod:
    """Tests for grace period configuration."""

    def test_default_grace_period_24_hours(self):
        """Default grace period should be 24 hours."""
        service = APIKeyService()
        assert service.grace_period_hours == 24

    def test_custom_grace_period(self):
        """Custom grace period should be configurable."""
        service = APIKeyService(grace_period_hours=48)
        assert service.grace_period_hours == 48

    def test_zero_grace_period_old_key_invalid_immediately(self):
        """With zero grace period, old key should be invalid immediately."""
        service = APIKeyService(grace_period_hours=0)

        original = service.create_api_key(name="Test Key")
        original_raw = original.raw_key

        service.rotate_api_key(original.id)

        # Old key should be invalid immediately
        assert service.validate_api_key(original_raw) is False


class TestAPIKeyListing:
    """Tests for listing API keys."""

    @pytest.fixture
    def api_key_service(self):
        """Create API key service instance."""
        return APIKeyService()

    def test_list_api_keys_empty(self, api_key_service):
        """Empty service should return empty list."""
        keys = api_key_service.list_api_keys()
        assert keys == []

    def test_list_api_keys_returns_all_active(self, api_key_service):
        """Should return all active API keys."""
        api_key_service.create_api_key(name="Key 1")
        api_key_service.create_api_key(name="Key 2")

        keys = api_key_service.list_api_keys()
        assert len(keys) == 2

    def test_list_api_keys_excludes_revoked(self, api_key_service):
        """Should not include revoked keys by default."""
        key1 = api_key_service.create_api_key(name="Key 1")
        api_key_service.create_api_key(name="Key 2")

        api_key_service.revoke_api_key(key1.id)

        keys = api_key_service.list_api_keys()
        assert len(keys) == 1
        assert keys[0].name == "Key 2"

    def test_list_api_keys_include_revoked(self, api_key_service):
        """Should include revoked keys when requested."""
        key1 = api_key_service.create_api_key(name="Key 1")
        api_key_service.create_api_key(name="Key 2")

        api_key_service.revoke_api_key(key1.id)

        keys = api_key_service.list_api_keys(include_revoked=True)
        assert len(keys) == 2
