"""
Admin management router for Helix.

Provides endpoints for admin user management:
- List users (SUPER_ADMIN only)
- Create user (SUPER_ADMIN only)
- Update user (SUPER_ADMIN only)
- Delete user (SUPER_ADMIN only)
"""
from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, EmailStr
from sqlalchemy.orm import Session

from core.permissions import Permission, require_permission
from core.security import hash_password
from database.connection import get_db
from database.models import AdminUser

router = APIRouter(prefix="/admin", tags=["Admin"])


# Request/Response schemas
class UserCreateRequest(BaseModel):
    """Request to create a new admin user."""

    username: str = Field(..., min_length=3, max_length=255)
    email: EmailStr
    password: str = Field(..., min_length=8)
    role: str = Field(default="VIEWER")
    is_active: bool = True


class UserUpdateRequest(BaseModel):
    """Request to update an admin user."""

    email: Optional[EmailStr] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    password: Optional[str] = Field(default=None, min_length=8)


class UserResponse(BaseModel):
    """Admin user response."""

    id: int
    username: str
    email: str
    role: str
    is_active: bool
    mfa_enabled: bool

    model_config = {"from_attributes": True}


@router.get("/users", response_model=List[UserResponse])
async def list_users(
    current_user: Annotated[AdminUser, Depends(require_permission(Permission.MANAGE_USERS))],
    db: Annotated[Session, Depends(get_db)],
) -> List[UserResponse]:
    """List all admin users.

    Requires MANAGE_USERS permission (SUPER_ADMIN role).
    """
    users = db.query(AdminUser).all()
    return [UserResponse.model_validate(u) for u in users]


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    request: UserCreateRequest,
    current_user: Annotated[AdminUser, Depends(require_permission(Permission.MANAGE_USERS))],
    db: Annotated[Session, Depends(get_db)],
) -> UserResponse:
    """Create a new admin user.

    Requires MANAGE_USERS permission (SUPER_ADMIN role).
    """
    # Check if username already exists
    existing = db.query(AdminUser).filter(AdminUser.username == request.username).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists",
        )

    # Check if email already exists
    existing = db.query(AdminUser).filter(AdminUser.email == request.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already exists",
        )

    user = AdminUser(
        username=request.username,
        email=request.email,
        password_hash=hash_password(request.password),
        role=request.role,
        is_active=request.is_active,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return UserResponse.model_validate(user)


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    current_user: Annotated[AdminUser, Depends(require_permission(Permission.MANAGE_USERS))],
    db: Annotated[Session, Depends(get_db)],
) -> UserResponse:
    """Get a specific admin user.

    Requires MANAGE_USERS permission (SUPER_ADMIN role).
    """
    user = db.query(AdminUser).filter(AdminUser.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return UserResponse.model_validate(user)


@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    request: UserUpdateRequest,
    current_user: Annotated[AdminUser, Depends(require_permission(Permission.MANAGE_USERS))],
    db: Annotated[Session, Depends(get_db)],
) -> UserResponse:
    """Update an admin user.

    Requires MANAGE_USERS permission (SUPER_ADMIN role).
    """
    user = db.query(AdminUser).filter(AdminUser.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Update fields if provided
    if request.email is not None:
        # Check for duplicate email
        existing = db.query(AdminUser).filter(
            AdminUser.email == request.email,
            AdminUser.id != user_id,
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already exists",
            )
        user.email = request.email

    if request.role is not None:
        user.role = request.role

    if request.is_active is not None:
        user.is_active = request.is_active

    if request.password is not None:
        user.password_hash = hash_password(request.password)

    db.commit()
    db.refresh(user)

    return UserResponse.model_validate(user)


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    current_user: Annotated[AdminUser, Depends(require_permission(Permission.MANAGE_USERS))],
    db: Annotated[Session, Depends(get_db)],
) -> None:
    """Delete an admin user.

    Requires MANAGE_USERS permission (SUPER_ADMIN role).
    Cannot delete yourself.
    """
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account",
        )

    user = db.query(AdminUser).filter(AdminUser.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    db.delete(user)
    db.commit()
