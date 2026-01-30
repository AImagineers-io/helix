"""
Integration tests for Role-Based Access Control (RBAC).

Tests cover:
- Role definitions (SUPER_ADMIN, ADMIN, EDITOR, VIEWER)
- Permission checks for different operations
- Role-based endpoint protection
- Permission inheritance
"""
import pytest
import os
import sys
from fastapi.testclient import TestClient

# Add backend to path
backend_path = os.path.join(os.path.dirname(__file__), '..', '..', '02_backend')
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)


class TestRoleDefinitions:
    """Tests for role hierarchy and definitions."""

    def test_role_enum_has_all_roles(self):
        """Test that Role enum includes all required roles."""
        from core.permissions import Role

        assert hasattr(Role, 'SUPER_ADMIN')
        assert hasattr(Role, 'ADMIN')
        assert hasattr(Role, 'EDITOR')
        assert hasattr(Role, 'VIEWER')

    def test_role_values_are_strings(self):
        """Test that role values are strings."""
        from core.permissions import Role

        assert isinstance(Role.SUPER_ADMIN.value, str)
        assert isinstance(Role.ADMIN.value, str)


class TestPermissionDefinitions:
    """Tests for permission definitions."""

    def test_permission_enum_has_required_permissions(self):
        """Test that Permission enum includes required permissions."""
        from core.permissions import Permission

        # User management
        assert hasattr(Permission, 'MANAGE_USERS')
        # Prompt management
        assert hasattr(Permission, 'MANAGE_PROMPTS')
        assert hasattr(Permission, 'EDIT_PROMPTS')
        assert hasattr(Permission, 'VIEW_PROMPTS')
        # QA management
        assert hasattr(Permission, 'MANAGE_QA')
        assert hasattr(Permission, 'EDIT_QA')
        assert hasattr(Permission, 'VIEW_QA')
        # Analytics
        assert hasattr(Permission, 'VIEW_ANALYTICS')


class TestRolePermissions:
    """Tests for role-permission mappings."""

    def test_super_admin_has_all_permissions(self):
        """Test that SUPER_ADMIN has all permissions."""
        from core.permissions import Role, Permission, has_permission

        for permission in Permission:
            assert has_permission(Role.SUPER_ADMIN, permission) is True

    def test_admin_has_management_permissions(self):
        """Test that ADMIN has management but not user management."""
        from core.permissions import Role, Permission, has_permission

        assert has_permission(Role.ADMIN, Permission.MANAGE_PROMPTS) is True
        assert has_permission(Role.ADMIN, Permission.MANAGE_QA) is True
        assert has_permission(Role.ADMIN, Permission.VIEW_ANALYTICS) is True
        # Admin should NOT manage users
        assert has_permission(Role.ADMIN, Permission.MANAGE_USERS) is False

    def test_editor_has_edit_permissions(self):
        """Test that EDITOR can edit but not manage."""
        from core.permissions import Role, Permission, has_permission

        assert has_permission(Role.EDITOR, Permission.EDIT_PROMPTS) is True
        assert has_permission(Role.EDITOR, Permission.EDIT_QA) is True
        # Editor should NOT manage
        assert has_permission(Role.EDITOR, Permission.MANAGE_PROMPTS) is False
        assert has_permission(Role.EDITOR, Permission.MANAGE_USERS) is False

    def test_viewer_has_view_only_permissions(self):
        """Test that VIEWER can only view."""
        from core.permissions import Role, Permission, has_permission

        assert has_permission(Role.VIEWER, Permission.VIEW_PROMPTS) is True
        assert has_permission(Role.VIEWER, Permission.VIEW_QA) is True
        assert has_permission(Role.VIEWER, Permission.VIEW_ANALYTICS) is True
        # Viewer should NOT edit or manage
        assert has_permission(Role.VIEWER, Permission.EDIT_PROMPTS) is False
        assert has_permission(Role.VIEWER, Permission.MANAGE_QA) is False


class TestProtectedEndpoints:
    """Tests for role-protected API endpoints."""

    def test_super_admin_can_access_user_management(self, rbac_client, super_admin_token):
        """Test that SUPER_ADMIN can access user management."""
        response = rbac_client.get(
            "/admin/users",
            headers={"Authorization": f"Bearer {super_admin_token}"},
        )
        # Should succeed (200)
        assert response.status_code == 200

    def test_admin_cannot_access_user_management(self, rbac_client, admin_token):
        """Test that ADMIN cannot access user management."""
        response = rbac_client.get(
            "/admin/users",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 403
        assert "permission" in response.json()["detail"].lower()

    def test_editor_cannot_access_user_management(self, rbac_client, editor_token):
        """Test that EDITOR cannot access user management."""
        response = rbac_client.get(
            "/admin/users",
            headers={"Authorization": f"Bearer {editor_token}"},
        )
        assert response.status_code == 403

    def test_viewer_cannot_access_user_management(self, rbac_client, viewer_token):
        """Test that VIEWER cannot access user management."""
        response = rbac_client.get(
            "/admin/users",
            headers={"Authorization": f"Bearer {viewer_token}"},
        )
        assert response.status_code == 403

    def test_super_admin_can_create_user(self, rbac_client, super_admin_token):
        """Test that SUPER_ADMIN can create users."""
        response = rbac_client.post(
            "/admin/users",
            json={
                "username": "newuser",
                "email": "new@test.com",
                "password": "password123",
                "role": "VIEWER",
            },
            headers={"Authorization": f"Bearer {super_admin_token}"},
        )
        assert response.status_code == 201

    def test_admin_cannot_create_user(self, rbac_client, admin_token):
        """Test that ADMIN cannot create users."""
        response = rbac_client.post(
            "/admin/users",
            json={
                "username": "newuser2",
                "email": "new2@test.com",
                "password": "password123",
                "role": "VIEWER",
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 403


class TestPermissionDependency:
    """Tests for the require_permission dependency."""

    def test_missing_permission_returns_403(self, rbac_client, viewer_token):
        """Test that insufficient permission returns 403 Forbidden."""
        # Try to access user management as viewer
        response = rbac_client.get(
            "/admin/users",
            headers={"Authorization": f"Bearer {viewer_token}"},
        )
        assert response.status_code == 403

    def test_error_message_indicates_required_permission(self, rbac_client, viewer_token):
        """Test that 403 response indicates what permission was needed."""
        response = rbac_client.get(
            "/admin/users",
            headers={"Authorization": f"Bearer {viewer_token}"},
        )
        assert response.status_code == 403
        data = response.json()
        assert "permission" in data["detail"].lower() or "denied" in data["detail"].lower()


# Fixtures
@pytest.fixture
def rbac_client():
    """Create test client with RBAC-enabled app."""
    # Set required env vars
    os.environ['APP_NAME'] = 'Helix Test'
    os.environ['BOT_NAME'] = 'Test Bot'
    os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
    os.environ['SECRET_KEY'] = 'test-secret-key-for-jwt-signing-minimum-32-chars'

    # Clear settings cache
    from core.config import get_settings
    get_settings.cache_clear()

    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.pool import StaticPool

    from database.connection import Base, get_db
    from database.models import AdminUser, PromptTemplate, PromptVersion
    from core.security import hash_password
    from api.main import create_app

    # Create fresh database
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    app = create_app()

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    # Seed users with different roles
    db = TestingSessionLocal()
    try:
        users = [
            AdminUser(
                username="super_admin",
                email="super@test.com",
                password_hash=hash_password("password"),
                is_active=True,
                role="SUPER_ADMIN",
            ),
            AdminUser(
                username="admin_user",
                email="admin@test.com",
                password_hash=hash_password("password"),
                is_active=True,
                role="ADMIN",
            ),
            AdminUser(
                username="editor_user",
                email="editor@test.com",
                password_hash=hash_password("password"),
                is_active=True,
                role="EDITOR",
            ),
            AdminUser(
                username="viewer_user",
                email="viewer@test.com",
                password_hash=hash_password("password"),
                is_active=True,
                role="VIEWER",
            ),
        ]
        for user in users:
            db.add(user)

        # Create a test prompt for update tests
        template = PromptTemplate(
            name="test_prompt",
            prompt_type="system",
            description="Test prompt",
        )
        db.add(template)
        db.flush()

        version = PromptVersion(
            template_id=template.id,
            content="Initial content",
            version_number=1,
            is_active=True,
        )
        db.add(version)
        db.commit()
    finally:
        db.close()

    client = TestClient(app)
    yield client

    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture
def super_admin_token(rbac_client):
    """Get token for super admin user."""
    response = rbac_client.post(
        "/auth/login",
        json={"username": "super_admin", "password": "password"},
    )
    return response.json()["access_token"]


@pytest.fixture
def admin_token(rbac_client):
    """Get token for admin user."""
    response = rbac_client.post(
        "/auth/login",
        json={"username": "admin_user", "password": "password"},
    )
    return response.json()["access_token"]


@pytest.fixture
def editor_token(rbac_client):
    """Get token for editor user."""
    response = rbac_client.post(
        "/auth/login",
        json={"username": "editor_user", "password": "password"},
    )
    return response.json()["access_token"]


@pytest.fixture
def viewer_token(rbac_client):
    """Get token for viewer user."""
    response = rbac_client.post(
        "/auth/login",
        json={"username": "viewer_user", "password": "password"},
    )
    return response.json()["access_token"]


