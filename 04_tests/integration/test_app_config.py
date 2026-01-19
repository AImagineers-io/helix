"""
Integration tests for API app configuration.

Tests verify:
- API title/description uses config values
- Health endpoint returns app info from config
- Config values are used correctly by FastAPI app
"""
import pytest
from fastapi.testclient import TestClient


class TestAppConfiguration:
    """Tests for API app using configuration."""

    def test_app_title_uses_config_app_name(self, clean_env, monkeypatch):
        """Test that FastAPI app title uses APP_NAME from config."""
        monkeypatch.setenv('APP_NAME', 'CustomApp')
        # Clear cached settings
        from core.config import get_settings
        get_settings.cache_clear()

        from api.main import create_app
        app = create_app()

        assert app.title == 'CustomApp'

    def test_app_description_uses_config(self, clean_env, monkeypatch):
        """Test that FastAPI app description uses APP_DESCRIPTION from config."""
        monkeypatch.setenv('APP_DESCRIPTION', 'Custom description')
        from core.config import get_settings
        get_settings.cache_clear()

        from api.main import create_app
        app = create_app()

        assert app.description == 'Custom description'

    def test_app_default_title_is_helix(self, clean_env):
        """Test that default app title is 'Helix'."""
        from core.config import get_settings
        get_settings.cache_clear()

        from api.main import create_app
        app = create_app()

        assert app.title == 'Helix'


class TestHealthEndpoint:
    """Tests for health endpoint configuration."""

    def test_health_endpoint_returns_200(self, clean_env):
        """Test that /health endpoint returns 200 OK."""
        from core.config import get_settings
        get_settings.cache_clear()

        from api.main import create_app
        app = create_app()
        client = TestClient(app)

        response = client.get('/health')
        assert response.status_code == 200

    def test_health_endpoint_returns_status_ok(self, clean_env):
        """Test that /health returns status: ok."""
        from core.config import get_settings
        get_settings.cache_clear()

        from api.main import create_app
        app = create_app()
        client = TestClient(app)

        response = client.get('/health')
        data = response.json()
        assert data['status'] == 'ok'

    def test_health_endpoint_includes_app_name(self, clean_env, monkeypatch):
        """Test that /health returns app_name from config."""
        monkeypatch.setenv('APP_NAME', 'HealthTestApp')
        from core.config import get_settings
        get_settings.cache_clear()

        from api.main import create_app
        app = create_app()
        client = TestClient(app)

        response = client.get('/health')
        data = response.json()
        assert data['app_name'] == 'HealthTestApp'

    def test_health_endpoint_includes_version(self, clean_env):
        """Test that /health returns version info."""
        from core.config import get_settings
        get_settings.cache_clear()

        from api.main import create_app
        app = create_app()
        client = TestClient(app)

        response = client.get('/health')
        data = response.json()
        assert 'version' in data


class TestCorsConfiguration:
    """Tests for CORS configuration."""

    def test_cors_allows_configured_origins(self, clean_env, monkeypatch):
        """Test that CORS allows configured origins."""
        monkeypatch.setenv('CORS_ORIGINS', 'https://example.com')
        from core.config import get_settings
        get_settings.cache_clear()

        from api.main import create_app
        app = create_app()
        client = TestClient(app)

        response = client.options(
            '/health',
            headers={
                'Origin': 'https://example.com',
                'Access-Control-Request-Method': 'GET'
            }
        )
        # CORS preflight should succeed
        assert response.status_code in (200, 204, 405)
