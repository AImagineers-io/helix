"""
Role-Based Access Control (RBAC) for Helix admin API.

This module defines:
- Role enumeration (SUPER_ADMIN, ADMIN, EDITOR, VIEWER)
- Permission enumeration for granular access control
- Role-permission mappings
- Permission checking utilities
- FastAPI dependency for endpoint protection

Usage:
    from core.permissions import require_permission, Permission

    @router.post("/users/")
    async def create_user(
        current_user: Annotated[AdminUser, Depends(require_permission(Permission.MANAGE_USERS))]
    ):
        ...

Role Hierarchy:
- SUPER_ADMIN: Full access to all features including user management
- ADMIN: Full access except user management
- EDITOR: Can edit prompts and QA pairs
- VIEWER: Read-only access
"""
from enum import Enum
from functools import wraps
from typing import Annotated, Callable, List

from fastapi import Depends, HTTPException, status


class Role(str, Enum):
    """User roles for access control.

    Attributes:
        SUPER_ADMIN: Full system access including user management.
        ADMIN: Full access to prompts, QA, analytics (no user management).
        EDITOR: Can edit prompts and QA pairs.
        VIEWER: Read-only access to all features.
    """

    SUPER_ADMIN = "SUPER_ADMIN"
    ADMIN = "ADMIN"
    EDITOR = "EDITOR"
    VIEWER = "VIEWER"


class Permission(str, Enum):
    """Granular permissions for access control.

    Attributes:
        MANAGE_USERS: Create, update, delete admin users.
        MANAGE_PROMPTS: Full prompt management including delete.
        EDIT_PROMPTS: Edit prompt content (create new versions).
        VIEW_PROMPTS: View prompts and versions.
        MANAGE_QA: Full QA pair management including delete.
        EDIT_QA: Create and edit QA pairs.
        VIEW_QA: View QA pairs.
        VIEW_ANALYTICS: View analytics dashboard.
        MANAGE_SETTINGS: Modify system settings.
        VIEW_SECURITY: View security dashboard and logs.
        MANAGE_SECURITY: Manage security settings and responses.
    """

    MANAGE_USERS = "manage_users"
    MANAGE_PROMPTS = "manage_prompts"
    EDIT_PROMPTS = "edit_prompts"
    VIEW_PROMPTS = "view_prompts"
    MANAGE_QA = "manage_qa"
    EDIT_QA = "edit_qa"
    VIEW_QA = "view_qa"
    VIEW_ANALYTICS = "view_analytics"
    MANAGE_SETTINGS = "manage_settings"
    VIEW_SECURITY = "view_security"
    MANAGE_SECURITY = "manage_security"


# Role-permission mappings
# Each role includes all permissions listed plus any from "child" roles
ROLE_PERMISSIONS: dict[Role, set[Permission]] = {
    Role.SUPER_ADMIN: {
        Permission.MANAGE_USERS,
        Permission.MANAGE_PROMPTS,
        Permission.EDIT_PROMPTS,
        Permission.VIEW_PROMPTS,
        Permission.MANAGE_QA,
        Permission.EDIT_QA,
        Permission.VIEW_QA,
        Permission.VIEW_ANALYTICS,
        Permission.MANAGE_SETTINGS,
        Permission.VIEW_SECURITY,
        Permission.MANAGE_SECURITY,
    },
    Role.ADMIN: {
        Permission.MANAGE_PROMPTS,
        Permission.EDIT_PROMPTS,
        Permission.VIEW_PROMPTS,
        Permission.MANAGE_QA,
        Permission.EDIT_QA,
        Permission.VIEW_QA,
        Permission.VIEW_ANALYTICS,
        Permission.VIEW_SECURITY,
    },
    Role.EDITOR: {
        Permission.EDIT_PROMPTS,
        Permission.VIEW_PROMPTS,
        Permission.EDIT_QA,
        Permission.VIEW_QA,
        Permission.VIEW_ANALYTICS,
    },
    Role.VIEWER: {
        Permission.VIEW_PROMPTS,
        Permission.VIEW_QA,
        Permission.VIEW_ANALYTICS,
    },
}


def has_permission(role: Role | str, permission: Permission) -> bool:
    """Check if a role has a specific permission.

    Args:
        role: Role to check (Role enum or string).
        permission: Permission to check for.

    Returns:
        True if the role has the permission, False otherwise.

    Examples:
        >>> has_permission(Role.ADMIN, Permission.MANAGE_QA)
        True
        >>> has_permission(Role.VIEWER, Permission.EDIT_PROMPTS)
        False
    """
    # Convert string to Role enum if needed
    if isinstance(role, str):
        try:
            role = Role(role)
        except ValueError:
            return False

    permissions = ROLE_PERMISSIONS.get(role, set())
    return permission in permissions


def get_role_permissions(role: Role | str) -> set[Permission]:
    """Get all permissions for a role.

    Args:
        role: Role to get permissions for.

    Returns:
        Set of permissions for the role.
    """
    if isinstance(role, str):
        try:
            role = Role(role)
        except ValueError:
            return set()

    return ROLE_PERMISSIONS.get(role, set()).copy()


def require_permission(permission: Permission):
    """FastAPI dependency factory for permission-based access control.

    Creates a dependency that checks if the current user has the required
    permission based on their role.

    Args:
        permission: The permission required to access the endpoint.

    Returns:
        FastAPI dependency function.

    Usage:
        @router.delete("/prompts/{id}")
        async def delete_prompt(
            current_user: Annotated[AdminUser, Depends(require_permission(Permission.MANAGE_PROMPTS))]
        ):
            ...
    """
    from api.routers.auth import get_current_user
    from database.models import AdminUser

    async def permission_checker(
        current_user: Annotated[AdminUser, Depends(get_current_user)]
    ) -> AdminUser:
        """Check if the current user has the required permission.

        Args:
            current_user: The authenticated user.

        Returns:
            The current user if permission check passes.

        Raises:
            HTTPException: If the user lacks the required permission.
        """
        if not has_permission(current_user.role, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied. Required: {permission.value}",
            )
        return current_user

    return permission_checker


def require_any_permission(*permissions: Permission):
    """FastAPI dependency factory requiring any of the specified permissions.

    Args:
        *permissions: Permissions, any of which grants access.

    Returns:
        FastAPI dependency function.
    """
    from api.routers.auth import get_current_user
    from database.models import AdminUser

    async def permission_checker(
        current_user: Annotated[AdminUser, Depends(get_current_user)]
    ) -> AdminUser:
        for permission in permissions:
            if has_permission(current_user.role, permission):
                return current_user

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Permission denied. Required one of: {', '.join(p.value for p in permissions)}",
        )

    return permission_checker


def require_role(role: Role):
    """FastAPI dependency factory for role-based access control.

    Args:
        role: Minimum role required for access.

    Returns:
        FastAPI dependency function.
    """
    from api.routers.auth import get_current_user
    from database.models import AdminUser

    # Role hierarchy (higher index = more privileged)
    role_hierarchy = [Role.VIEWER, Role.EDITOR, Role.ADMIN, Role.SUPER_ADMIN]

    async def role_checker(
        current_user: Annotated[AdminUser, Depends(get_current_user)]
    ) -> AdminUser:
        try:
            user_role = Role(current_user.role)
            required_level = role_hierarchy.index(role)
            user_level = role_hierarchy.index(user_role)

            if user_level < required_level:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission denied. Required role: {role.value}",
                )
        except (ValueError, IndexError):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid user role",
            )

        return current_user

    return role_checker
