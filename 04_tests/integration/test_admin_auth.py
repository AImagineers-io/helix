"""
Integration tests for admin JWT authentication.

Tests cover:
- Login endpoint with username/password
- JWT token generation and validation
- Token refresh mechanism
- Logout functionality
- Token expiry
"""
import pytest
import time
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient


class TestAdminLogin:
    """Tests for /auth/login endpoint."""

    def test_login_with_valid_credentials_returns_tokens(self, auth_test_client):
        """Test that valid credentials return access and refresh tokens."""
        response = auth_test_client.post(
            "/auth/login",
            json={"username": "admin", "password": "test_password"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data

    def test_login_with_invalid_password_returns_401(self, auth_test_client):
        """Test that invalid password returns 401 Unauthorized."""
        response = auth_test_client.post(
            "/auth/login",
            json={"username": "admin", "password": "wrong_password"},
        )

        assert response.status_code == 401
        assert "Invalid credentials" in response.json()["detail"]

    def test_login_with_unknown_user_returns_401(self, auth_test_client):
        """Test that unknown username returns 401 Unauthorized."""
        response = auth_test_client.post(
            "/auth/login",
            json={"username": "nonexistent", "password": "any_password"},
        )

        assert response.status_code == 401
        assert "Invalid credentials" in response.json()["detail"]

    def test_login_with_missing_password_returns_422(self, auth_test_client):
        """Test that missing password returns validation error."""
        response = auth_test_client.post(
            "/auth/login",
            json={"username": "admin"},
        )

        assert response.status_code == 422

    def test_login_with_empty_credentials_returns_422(self, auth_test_client):
        """Test that empty credentials return validation error."""
        response = auth_test_client.post(
            "/auth/login",
            json={"username": "", "password": ""},
        )

        assert response.status_code == 422


class TestJWTTokenValidation:
    """Tests for JWT token validation."""

    def test_access_protected_endpoint_with_valid_token(self, auth_test_client, admin_token):
        """Test that valid token grants access to protected endpoints."""
        response = auth_test_client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "username" in data
        assert data["username"] == "admin"

    def test_access_protected_endpoint_without_token_returns_401(self, auth_test_client):
        """Test that missing token returns 401."""
        response = auth_test_client.get("/auth/me")

        assert response.status_code == 401
        assert "Not authenticated" in response.json()["detail"]

    def test_access_protected_endpoint_with_invalid_token_returns_401(self, auth_test_client):
        """Test that invalid token returns 401."""
        response = auth_test_client.get(
            "/auth/me",
            headers={"Authorization": "Bearer invalid_token_here"},
        )

        assert response.status_code == 401
        assert "Could not validate credentials" in response.json()["detail"]

    def test_access_protected_endpoint_with_expired_token_returns_401(
        self, auth_test_client, expired_token
    ):
        """Test that expired token returns 401."""
        response = auth_test_client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {expired_token}"},
        )

        assert response.status_code == 401
        assert "expired" in response.json()["detail"].lower()

    def test_access_protected_endpoint_with_malformed_header_returns_401(
        self, auth_test_client
    ):
        """Test that malformed Authorization header returns 401."""
        response = auth_test_client.get(
            "/auth/me",
            headers={"Authorization": "NotBearer token"},
        )

        assert response.status_code == 401


class TestTokenRefresh:
    """Tests for token refresh endpoint."""

    def test_refresh_with_valid_refresh_token_returns_new_tokens(
        self, auth_test_client, admin_refresh_token
    ):
        """Test that valid refresh token returns new access token."""
        response = auth_test_client.post(
            "/auth/refresh",
            json={"refresh_token": admin_refresh_token},
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"

    def test_refresh_with_invalid_token_returns_401(self, auth_test_client):
        """Test that invalid refresh token returns 401."""
        response = auth_test_client.post(
            "/auth/refresh",
            json={"refresh_token": "invalid_refresh_token"},
        )

        assert response.status_code == 401
        assert "Invalid refresh token" in response.json()["detail"]

    def test_refresh_with_access_token_returns_401(self, auth_test_client, admin_token):
        """Test that using access token as refresh token fails."""
        response = auth_test_client.post(
            "/auth/refresh",
            json={"refresh_token": admin_token},
        )

        assert response.status_code == 401

    def test_refresh_with_expired_refresh_token_returns_401(
        self, auth_test_client, expired_refresh_token
    ):
        """Test that expired refresh token returns 401."""
        response = auth_test_client.post(
            "/auth/refresh",
            json={"refresh_token": expired_refresh_token},
        )

        assert response.status_code == 401


class TestLogout:
    """Tests for logout endpoint."""

    def test_logout_invalidates_token(self, auth_test_client, admin_token):
        """Test that logout invalidates the current token."""
        # First verify token works
        response = auth_test_client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200

        # Logout
        response = auth_test_client.post(
            "/auth/logout",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        assert response.json()["message"] == "Successfully logged out"

    def test_logout_without_token_returns_401(self, auth_test_client):
        """Test that logout without token returns 401."""
        response = auth_test_client.post("/auth/logout")
        assert response.status_code == 401


class TestTokenExpiry:
    """Tests for token expiration configuration."""

    def test_access_token_contains_correct_expiry(self, auth_test_client):
        """Test that access token expires in 1 hour."""
        response = auth_test_client.post(
            "/auth/login",
            json={"username": "admin", "password": "test_password"},
        )

        assert response.status_code == 200
        data = response.json()
        # Access token should expire in 3600 seconds (1 hour)
        assert data["expires_in"] == 3600

    def test_token_payload_contains_required_claims(self, auth_test_client, admin_token):
        """Test that token contains required JWT claims."""
        # Decode token without verification to check claims
        import jwt

        payload = jwt.decode(admin_token, options={"verify_signature": False})

        assert "sub" in payload  # Subject (username)
        assert "exp" in payload  # Expiration
        assert "iat" in payload  # Issued at
        assert "type" in payload  # Token type (access/refresh)
        assert payload["type"] == "access"


# Fixtures for auth tests
@pytest.fixture
def auth_test_client():
    """Create test client with auth-enabled app."""
    import os
    import sys

    # Add backend to path
    backend_path = os.path.join(os.path.dirname(__file__), '..', '..', '02_backend')
    if backend_path not in sys.path:
        sys.path.insert(0, backend_path)

    # Set required env vars
    os.environ['APP_NAME'] = 'Helix Test'
    os.environ['BOT_NAME'] = 'Test Bot'
    os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
    os.environ['SECRET_KEY'] = 'test-secret-key-for-jwt-signing-minimum-32-chars'

    # Clear settings cache
    from core.config import get_settings
    get_settings.cache_clear()

    # Import after setting env vars
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.pool import StaticPool

    from database.connection import Base
    from database.models import AdminUser
    from core.security import hash_password
    from api.main import create_app

    # Create a fresh in-memory database for this test
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # Create tables
    Base.metadata.create_all(bind=engine)

    # Create app with overridden dependency
    app = create_app()

    # Override get_db dependency
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    from database.connection import get_db
    app.dependency_overrides[get_db] = override_get_db

    # Seed admin user
    db = TestingSessionLocal()
    try:
        admin = AdminUser(
            username="admin",
            email="admin@test.com",
            password_hash=hash_password("test_password"),
            is_active=True,
        )
        db.add(admin)
        db.commit()
    finally:
        db.close()

    client = TestClient(app)
    yield client

    # Cleanup
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture
def admin_token(auth_test_client):
    """Get a valid admin access token."""
    response = auth_test_client.post(
        "/auth/login",
        json={"username": "admin", "password": "test_password"},
    )
    return response.json()["access_token"]


@pytest.fixture
def admin_refresh_token(auth_test_client):
    """Get a valid admin refresh token."""
    response = auth_test_client.post(
        "/auth/login",
        json={"username": "admin", "password": "test_password"},
    )
    return response.json()["refresh_token"]


@pytest.fixture
def expired_token():
    """Generate an expired access token."""
    import os
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '02_backend'))

    from core.security import create_access_token
    from datetime import timedelta

    return create_access_token(
        data={"sub": "admin"},
        expires_delta=timedelta(seconds=-1),  # Already expired
    )


@pytest.fixture
def expired_refresh_token():
    """Generate an expired refresh token."""
    import os
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '02_backend'))

    from core.security import create_refresh_token
    from datetime import timedelta

    return create_refresh_token(
        data={"sub": "admin"},
        expires_delta=timedelta(seconds=-1),  # Already expired
    )
