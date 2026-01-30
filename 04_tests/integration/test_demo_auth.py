"""Integration tests for demo environment access control.

Tests that demo environments require basic auth for protected routes.
"""
import base64
import pytest
from fastapi.testclient import TestClient


class TestDemoAuthMiddleware:
    """Tests for DemoAuthMiddleware."""

    @pytest.fixture
    def demo_app(self, clean_env):
        """Create app configured for demo environment."""
        clean_env.setenv('ENVIRONMENT', 'demo')
        clean_env.setenv('DATABASE_URL', 'sqlite:///:memory:')
        clean_env.setenv('DEMO_USERNAME', 'demo')
        clean_env.setenv('DEMO_PASSWORD', 'demopass123')

        from core.config import get_settings
        get_settings.cache_clear()

        from api.main import create_app
        app = create_app()
        return TestClient(app)

    @pytest.fixture
    def dev_app(self, clean_env):
        """Create app configured for development environment."""
        clean_env.setenv('ENVIRONMENT', 'development')
        clean_env.setenv('DATABASE_URL', 'sqlite:///:memory:')

        from core.config import get_settings
        get_settings.cache_clear()

        from api.main import create_app
        app = create_app()
        return TestClient(app)

    def _basic_auth_header(self, username: str, password: str) -> dict:
        """Create basic auth header."""
        credentials = base64.b64encode(f"{username}:{password}".encode()).decode()
        return {"Authorization": f"Basic {credentials}"}

    # Public routes (no auth required even in demo)
    def test_health_endpoint_public_in_demo(self, demo_app):
        """Health endpoint should be accessible without auth in demo."""
        response = demo_app.get("/health")
        assert response.status_code == 200

    def test_branding_endpoint_public_in_demo(self, demo_app):
        """Branding endpoint should be accessible without auth in demo."""
        response = demo_app.get("/branding")
        assert response.status_code == 200

    # Protected routes require auth in demo
    def test_protected_route_requires_auth_in_demo(self, demo_app):
        """Protected routes should require auth in demo environment."""
        response = demo_app.get("/prompts")
        assert response.status_code == 401
        assert "WWW-Authenticate" in response.headers
        assert response.headers["WWW-Authenticate"] == 'Basic realm="Demo Environment"'

    def test_protected_route_with_valid_auth_succeeds(self, demo_app):
        """Protected routes with valid basic auth should succeed."""
        headers = self._basic_auth_header("demo", "demopass123")
        # Still need API key for prompts endpoint
        headers["X-API-Key"] = "test-key"
        response = demo_app.get("/prompts", headers=headers)
        # May return 401 for missing API key config, but should pass demo auth
        # The important thing is it's not 401 with WWW-Authenticate
        assert "WWW-Authenticate" not in response.headers or response.status_code != 401

    def test_protected_route_with_invalid_password_fails(self, demo_app):
        """Protected routes with invalid password should fail."""
        headers = self._basic_auth_header("demo", "wrongpassword")
        response = demo_app.get("/prompts", headers=headers)
        assert response.status_code == 401

    def test_protected_route_with_invalid_username_fails(self, demo_app):
        """Protected routes with invalid username should fail."""
        headers = self._basic_auth_header("wronguser", "demopass123")
        response = demo_app.get("/prompts", headers=headers)
        assert response.status_code == 401

    # Development environment has no demo auth
    def test_protected_route_no_demo_auth_in_development(self, dev_app):
        """Development environment should not require demo auth."""
        response = dev_app.get("/prompts")
        # Should fail with API key error, not demo auth
        assert response.status_code == 401
        assert "WWW-Authenticate" not in response.headers

    def test_health_works_without_auth_in_development(self, dev_app):
        """Health endpoint works in development without any auth."""
        response = dev_app.get("/health")
        assert response.status_code == 200


class TestDemoAuthConfig:
    """Tests for demo auth configuration."""

    def test_demo_auth_disabled_without_credentials(self, clean_env):
        """Demo auth should be disabled if credentials not configured."""
        clean_env.setenv('ENVIRONMENT', 'demo')
        clean_env.setenv('DATABASE_URL', 'sqlite:///:memory:')
        # Don't set DEMO_USERNAME/DEMO_PASSWORD

        from core.config import get_settings
        get_settings.cache_clear()

        settings = get_settings()
        assert settings.demo_auth.enabled is False

    def test_demo_auth_enabled_with_credentials(self, clean_env):
        """Demo auth should be enabled when credentials are configured."""
        clean_env.setenv('ENVIRONMENT', 'demo')
        clean_env.setenv('DATABASE_URL', 'sqlite:///:memory:')
        clean_env.setenv('DEMO_USERNAME', 'demo')
        clean_env.setenv('DEMO_PASSWORD', 'demopass')

        from core.config import get_settings
        get_settings.cache_clear()

        settings = get_settings()
        assert settings.demo_auth.enabled is True
        assert settings.demo_auth.username == 'demo'
        assert settings.demo_auth.password == 'demopass'

    def test_demo_auth_public_paths_configurable(self, clean_env):
        """Demo auth public paths should be configurable."""
        clean_env.setenv('ENVIRONMENT', 'demo')
        clean_env.setenv('DATABASE_URL', 'sqlite:///:memory:')
        clean_env.setenv('DEMO_USERNAME', 'demo')
        clean_env.setenv('DEMO_PASSWORD', 'demopass')

        from core.config import get_settings
        get_settings.cache_clear()

        settings = get_settings()
        # Default public paths
        assert '/health' in settings.demo_auth.public_paths
        assert '/branding' in settings.demo_auth.public_paths
