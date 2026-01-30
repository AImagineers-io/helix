"""
Unit tests for core security module.

Tests cover:
- Password hashing and verification
- JWT token creation and validation
- Token type handling (access vs refresh)
"""
import pytest
import os
import sys
from datetime import datetime, timedelta, timezone

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '02_backend'))

# Set required env vars before imports
os.environ['APP_NAME'] = 'Helix Test'
os.environ['BOT_NAME'] = 'Test Bot'
os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
os.environ['SECRET_KEY'] = 'test-secret-key-for-jwt-signing-minimum-32-chars'


class TestPasswordHashing:
    """Tests for password hashing functions."""

    def test_hash_password_returns_different_hash(self):
        """Test that hashing password returns a hash different from input."""
        from core.security import hash_password

        password = "my_secure_password"
        hashed = hash_password(password)

        assert hashed != password
        assert len(hashed) > 0

    def test_hash_password_produces_unique_hashes(self):
        """Test that same password produces different hashes (salted)."""
        from core.security import hash_password

        password = "my_secure_password"
        hash1 = hash_password(password)
        hash2 = hash_password(password)

        # Bcrypt uses random salt, so hashes should differ
        assert hash1 != hash2

    def test_verify_password_returns_true_for_correct_password(self):
        """Test that verify_password returns True for matching password."""
        from core.security import hash_password, verify_password

        password = "my_secure_password"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True

    def test_verify_password_returns_false_for_wrong_password(self):
        """Test that verify_password returns False for wrong password."""
        from core.security import hash_password, verify_password

        password = "my_secure_password"
        hashed = hash_password(password)

        assert verify_password("wrong_password", hashed) is False

    def test_verify_password_returns_false_for_empty_password(self):
        """Test that verify_password handles empty password."""
        from core.security import hash_password, verify_password

        hashed = hash_password("my_secure_password")

        assert verify_password("", hashed) is False

    def test_hash_password_handles_unicode(self):
        """Test that password hashing works with unicode characters."""
        from core.security import hash_password, verify_password

        password = "pässwörd_with_üñíçödé_🔐"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True


class TestJWTTokenCreation:
    """Tests for JWT token creation."""

    def test_create_access_token_returns_valid_jwt(self):
        """Test that create_access_token returns a valid JWT string."""
        from core.security import create_access_token

        token = create_access_token(data={"sub": "testuser"})

        assert isinstance(token, str)
        assert len(token) > 0
        # JWT has 3 parts separated by dots
        assert len(token.split(".")) == 3

    def test_create_access_token_includes_subject(self):
        """Test that access token includes the subject claim."""
        import jwt
        from core.security import create_access_token

        token = create_access_token(data={"sub": "testuser"})
        payload = jwt.decode(token, options={"verify_signature": False})

        assert payload["sub"] == "testuser"

    def test_create_access_token_includes_expiry(self):
        """Test that access token includes expiry claim."""
        import jwt
        from core.security import create_access_token

        token = create_access_token(data={"sub": "testuser"})
        payload = jwt.decode(token, options={"verify_signature": False})

        assert "exp" in payload
        # Expiry should be in the future
        assert payload["exp"] > datetime.now(timezone.utc).timestamp()

    def test_create_access_token_with_custom_expiry(self):
        """Test that custom expiry delta is respected."""
        import jwt
        from core.security import create_access_token

        expires = timedelta(minutes=5)
        token = create_access_token(data={"sub": "testuser"}, expires_delta=expires)
        payload = jwt.decode(token, options={"verify_signature": False})

        # Should expire roughly 5 minutes from now
        expected_exp = datetime.now(timezone.utc) + expires
        assert abs(payload["exp"] - expected_exp.timestamp()) < 5

    def test_create_access_token_type_is_access(self):
        """Test that access token has type 'access'."""
        import jwt
        from core.security import create_access_token

        token = create_access_token(data={"sub": "testuser"})
        payload = jwt.decode(token, options={"verify_signature": False})

        assert payload["type"] == "access"

    def test_create_refresh_token_type_is_refresh(self):
        """Test that refresh token has type 'refresh'."""
        import jwt
        from core.security import create_refresh_token

        token = create_refresh_token(data={"sub": "testuser"})
        payload = jwt.decode(token, options={"verify_signature": False})

        assert payload["type"] == "refresh"

    def test_refresh_token_has_longer_expiry(self):
        """Test that refresh token expires later than access token."""
        import jwt
        from core.security import create_access_token, create_refresh_token

        access_token = create_access_token(data={"sub": "testuser"})
        refresh_token = create_refresh_token(data={"sub": "testuser"})

        access_payload = jwt.decode(access_token, options={"verify_signature": False})
        refresh_payload = jwt.decode(refresh_token, options={"verify_signature": False})

        # Refresh token should expire after access token
        assert refresh_payload["exp"] > access_payload["exp"]


class TestJWTTokenValidation:
    """Tests for JWT token validation."""

    def test_verify_token_returns_payload_for_valid_token(self):
        """Test that verify_token returns payload for valid token."""
        from core.security import create_access_token, verify_token

        token = create_access_token(data={"sub": "testuser"})
        payload = verify_token(token)

        assert payload is not None
        assert payload["sub"] == "testuser"

    def test_verify_token_returns_none_for_invalid_token(self):
        """Test that verify_token returns None for invalid token."""
        from core.security import verify_token

        payload = verify_token("invalid.token.here")

        assert payload is None

    def test_verify_token_returns_none_for_expired_token(self):
        """Test that verify_token returns None for expired token."""
        from core.security import create_access_token, verify_token

        # Create token that's already expired
        token = create_access_token(
            data={"sub": "testuser"},
            expires_delta=timedelta(seconds=-1),
        )
        payload = verify_token(token)

        assert payload is None

    def test_verify_token_returns_none_for_wrong_signature(self):
        """Test that verify_token returns None for tampered token."""
        from core.security import create_access_token, verify_token

        token = create_access_token(data={"sub": "testuser"})
        # Tamper with the token
        parts = token.split(".")
        parts[2] = "tampered_signature"
        tampered_token = ".".join(parts)

        payload = verify_token(tampered_token)

        assert payload is None

    def test_verify_access_token_rejects_refresh_token(self):
        """Test that verify_access_token rejects refresh tokens."""
        from core.security import create_refresh_token, verify_access_token

        refresh_token = create_refresh_token(data={"sub": "testuser"})
        payload = verify_access_token(refresh_token)

        assert payload is None

    def test_verify_refresh_token_rejects_access_token(self):
        """Test that verify_refresh_token rejects access tokens."""
        from core.security import create_access_token, verify_refresh_token

        access_token = create_access_token(data={"sub": "testuser"})
        payload = verify_refresh_token(access_token)

        assert payload is None


class TestTokenConstants:
    """Tests for token configuration constants."""

    def test_access_token_expire_minutes_default(self):
        """Test that access token default expiry is 60 minutes (1 hour)."""
        from core.security import ACCESS_TOKEN_EXPIRE_MINUTES

        assert ACCESS_TOKEN_EXPIRE_MINUTES == 60

    def test_refresh_token_expire_days_default(self):
        """Test that refresh token default expiry is 7 days."""
        from core.security import REFRESH_TOKEN_EXPIRE_DAYS

        assert REFRESH_TOKEN_EXPIRE_DAYS == 7
