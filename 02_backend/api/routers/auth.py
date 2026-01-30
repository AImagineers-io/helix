"""
Authentication router for Helix admin API.

Provides JWT-based authentication endpoints:
- POST /auth/login - Authenticate with username/password
- POST /auth/refresh - Refresh access token using refresh token
- POST /auth/logout - Invalidate current session
- GET /auth/me - Get current user info

Token Configuration:
- Access token: 1 hour expiry
- Refresh token: 7 day expiry
"""
from datetime import datetime, timedelta, timezone
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from core.security import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    create_access_token,
    create_refresh_token,
    verify_access_token,
    verify_password,
    verify_refresh_token,
)
from database.connection import get_db
from database.models import AdminUser

router = APIRouter(prefix="/auth", tags=["Authentication"])

# HTTP Bearer security scheme
security = HTTPBearer(auto_error=False)


# Request/Response schemas
class LoginRequest(BaseModel):
    """Login request payload.

    Attributes:
        username: Admin username.
        password: Admin password.
    """

    username: str = Field(..., min_length=1, description="Admin username")
    password: str = Field(..., min_length=1, description="Admin password")


class TokenResponse(BaseModel):
    """Token response after successful authentication.

    Attributes:
        access_token: JWT access token.
        refresh_token: JWT refresh token.
        token_type: Token type (always 'bearer').
        expires_in: Access token expiry in seconds.
    """

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = ACCESS_TOKEN_EXPIRE_MINUTES * 60


class RefreshRequest(BaseModel):
    """Refresh token request payload.

    Attributes:
        refresh_token: Valid refresh token.
    """

    refresh_token: str = Field(..., description="Valid refresh token")


class UserResponse(BaseModel):
    """Current user information response.

    Attributes:
        id: User ID.
        username: Username.
        email: User email.
        role: User role.
        is_active: Whether user is active.
        mfa_enabled: Whether MFA is enabled.
    """

    id: int
    username: str
    email: str
    role: str
    is_active: bool
    mfa_enabled: bool


class LogoutResponse(BaseModel):
    """Logout response.

    Attributes:
        message: Success message.
    """

    message: str = "Successfully logged out"


# Dependency to get current user from token
async def get_current_user(
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(security)],
    db: Annotated[Session, Depends(get_db)],
) -> AdminUser:
    """Get the current authenticated user from JWT token.

    Args:
        credentials: HTTP Bearer credentials from Authorization header.
        db: Database session.

    Returns:
        The authenticated AdminUser.

    Raises:
        HTTPException: If authentication fails.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    payload = verify_access_token(token)

    if payload is None:
        # Check if it's an expired token by decoding without verification
        import jwt as pyjwt
        try:
            # First try to decode - this will tell us if the token structure is valid
            pyjwt.decode(
                token,
                options={
                    "verify_signature": False,
                    "verify_exp": False,
                }
            )
            # Token structure is valid, so it's likely expired or wrong type
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except pyjwt.exceptions.DecodeError:
            # Invalid token structure
            raise credentials_exception
        except HTTPException:
            # Re-raise our HTTPException
            raise
        except Exception:
            raise credentials_exception

    username: str = payload.get("sub")
    if username is None:
        raise credentials_exception

    user = db.query(AdminUser).filter(AdminUser.username == username).first()
    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is disabled",
        )

    return user


@router.post("/login", response_model=TokenResponse)
def login(
    request: LoginRequest,
    db: Annotated[Session, Depends(get_db)],
) -> TokenResponse:
    """Authenticate user and return JWT tokens.

    Args:
        request: Login credentials.
        db: Database session.

    Returns:
        TokenResponse with access and refresh tokens.

    Raises:
        HTTPException: If authentication fails.
    """
    # Find user by username
    user = db.query(AdminUser).filter(AdminUser.username == request.username).first()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if account is locked
    if user.is_locked():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is temporarily locked",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify password
    if not verify_password(request.password, user.password_hash):
        # Increment failed login attempts
        user.failed_login_attempts += 1

        # Lock account after 5 failed attempts for 15 minutes
        if user.failed_login_attempts >= 5:
            user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=15)

        db.commit()

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is disabled",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Reset failed login attempts on successful login
    user.failed_login_attempts = 0
    user.locked_until = None
    user.last_login = datetime.now(timezone.utc)
    db.commit()

    # Generate tokens
    access_token = create_access_token(data={"sub": user.username})
    refresh_token = create_refresh_token(data={"sub": user.username})

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(
    request: RefreshRequest,
    db: Annotated[Session, Depends(get_db)],
) -> TokenResponse:
    """Refresh access token using refresh token.

    Args:
        request: Refresh token request.
        db: Database session.

    Returns:
        TokenResponse with new access and refresh tokens.

    Raises:
        HTTPException: If refresh token is invalid.
    """
    payload = verify_refresh_token(request.refresh_token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    username: str = payload.get("sub")
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify user still exists and is active
    user = db.query(AdminUser).filter(AdminUser.username == username).first()
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Generate new tokens
    access_token = create_access_token(data={"sub": user.username})
    new_refresh_token = create_refresh_token(data={"sub": user.username})

    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
    )


@router.post("/logout", response_model=LogoutResponse)
def logout(
    current_user: Annotated[AdminUser, Depends(get_current_user)],
) -> LogoutResponse:
    """Logout current user.

    Note: Since JWTs are stateless, the token remains valid until expiry.
    For true logout, implement token blacklisting (see P12.1.5 session management).

    Args:
        current_user: Currently authenticated user.

    Returns:
        LogoutResponse with success message.
    """
    # In a stateless JWT implementation, logout is client-side
    # For server-side invalidation, use token blacklisting (session management)
    return LogoutResponse()


@router.get("/me", response_model=UserResponse)
def get_me(
    current_user: Annotated[AdminUser, Depends(get_current_user)],
) -> UserResponse:
    """Get current user information.

    Args:
        current_user: Currently authenticated user.

    Returns:
        UserResponse with user details.
    """
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        role=current_user.role,
        is_active=current_user.is_active,
        mfa_enabled=current_user.mfa_enabled,
    )
