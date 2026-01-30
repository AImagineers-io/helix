"""
Security utilities for Helix authentication and authorization.

This module provides:
- Password hashing and verification using bcrypt
- JWT token creation and validation
- Token type handling (access vs refresh)

Security Notes:
- Passwords are hashed using bcrypt with random salts
- JWTs use HS256 algorithm signed with SECRET_KEY
- Access tokens expire in 1 hour, refresh tokens in 7 days
- Token type is embedded in payload to prevent misuse

Usage:
    from core.security import hash_password, verify_password
    from core.security import create_access_token, verify_token

    # Password operations
    hashed = hash_password("my_password")
    is_valid = verify_password("my_password", hashed)

    # Token operations
    token = create_access_token(data={"sub": "username"})
    payload = verify_token(token)
"""
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Final, Optional

import bcrypt
import jwt
from pydantic import BaseModel

# Token expiration configuration
ACCESS_TOKEN_EXPIRE_MINUTES: Final[int] = 60  # 1 hour
REFRESH_TOKEN_EXPIRE_DAYS: Final[int] = 7     # 7 days

# JWT encoding algorithm
ALGORITHM: Final[str] = "HS256"

# Token type identifiers
TOKEN_TYPE_ACCESS: Final[str] = "access"
TOKEN_TYPE_REFRESH: Final[str] = "refresh"


def _get_secret_key() -> str:
    """Get the secret key for JWT signing.

    Returns:
        Secret key from environment or default for development.
    """
    return os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")


def hash_password(password: str) -> str:
    """Hash a password using bcrypt.

    Args:
        password: Plain text password to hash.

    Returns:
        Bcrypt hash of the password.
    """
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash.

    Args:
        plain_password: Plain text password to verify.
        hashed_password: Bcrypt hash to verify against.

    Returns:
        True if password matches, False otherwise.
    """
    if not plain_password:
        return False
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8"),
        )
    except Exception:
        return False


def create_access_token(
    data: dict[str, Any],
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Create a JWT access token.

    Args:
        data: Dictionary of claims to include in the token.
        expires_delta: Optional custom expiration time.

    Returns:
        Encoded JWT token string.
    """
    to_encode = data.copy()
    now = datetime.now(timezone.utc)

    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({
        "exp": expire,
        "iat": now,
        "type": TOKEN_TYPE_ACCESS,
    })

    return jwt.encode(to_encode, _get_secret_key(), algorithm=ALGORITHM)


def create_refresh_token(
    data: dict[str, Any],
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Create a JWT refresh token.

    Args:
        data: Dictionary of claims to include in the token.
        expires_delta: Optional custom expiration time.

    Returns:
        Encoded JWT token string.
    """
    to_encode = data.copy()
    now = datetime.now(timezone.utc)

    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    to_encode.update({
        "exp": expire,
        "iat": now,
        "type": TOKEN_TYPE_REFRESH,
    })

    return jwt.encode(to_encode, _get_secret_key(), algorithm=ALGORITHM)


def verify_token(token: str) -> Optional[dict[str, Any]]:
    """Verify and decode a JWT token.

    Args:
        token: JWT token string to verify.

    Returns:
        Decoded payload if valid, None if invalid or expired.
    """
    try:
        payload = jwt.decode(
            token,
            _get_secret_key(),
            algorithms=[ALGORITHM],
        )
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def verify_access_token(token: str) -> Optional[dict[str, Any]]:
    """Verify a JWT token is a valid access token.

    Args:
        token: JWT token string to verify.

    Returns:
        Decoded payload if valid access token, None otherwise.
    """
    payload = verify_token(token)
    if payload is None:
        return None
    if payload.get("type") != TOKEN_TYPE_ACCESS:
        return None
    return payload


def verify_refresh_token(token: str) -> Optional[dict[str, Any]]:
    """Verify a JWT token is a valid refresh token.

    Args:
        token: JWT token string to verify.

    Returns:
        Decoded payload if valid refresh token, None otherwise.
    """
    payload = verify_token(token)
    if payload is None:
        return None
    if payload.get("type") != TOKEN_TYPE_REFRESH:
        return None
    return payload


class TokenData(BaseModel):
    """Extracted data from a validated token.

    Attributes:
        username: The subject (username) from the token.
        token_type: Type of token (access or refresh).
    """

    username: Optional[str] = None
    token_type: str = "access"
