"""
Integration tests for branding API endpoint.

Tests verify:
- /branding endpoint returns current instance branding
- All branding fields are included in response
- Branding values match configuration
"""
import pytest
from fastapi.testclient import TestClient


class TestBrandingEndpoint:
    """Tests for branding API endpoint."""

    def test_branding_endpoint_returns_200(self, clean_env):
        """Test that /branding endpoint returns 200 OK."""
        from core.config import get_settings
        get_settings.cache_clear()

        from api.main import create_app
        app = create_app()
        client = TestClient(app)

        response = client.get('/branding')
        assert response.status_code == 200

    def test_branding_endpoint_returns_app_name(self, clean_env, monkeypatch):
        """Test that /branding returns configured app_name."""
        monkeypatch.setenv('APP_NAME', 'BrandedApp')
        from core.config import get_settings
        get_settings.cache_clear()

        from api.main import create_app
        app = create_app()
        client = TestClient(app)

        response = client.get('/branding')
        data = response.json()
        assert data['app_name'] == 'BrandedApp'

    def test_branding_endpoint_returns_bot_name(self, clean_env, monkeypatch):
        """Test that /branding returns configured bot_name."""
        monkeypatch.setenv('BOT_NAME', 'Aria')
        from core.config import get_settings
        get_settings.cache_clear()

        from api.main import create_app
        app = create_app()
        client = TestClient(app)

        response = client.get('/branding')
        data = response.json()
        assert data['bot_name'] == 'Aria'

    def test_branding_endpoint_returns_all_fields(self, clean_env):
        """Test that /branding returns all branding fields."""
        from core.config import get_settings
        get_settings.cache_clear()

        from api.main import create_app
        app = create_app()
        client = TestClient(app)

        response = client.get('/branding')
        data = response.json()

        assert 'app_name' in data
        assert 'app_description' in data
        assert 'bot_name' in data
        assert 'logo_url' in data
        assert 'primary_color' in data

    def test_branding_endpoint_returns_logo_url(self, clean_env, monkeypatch):
        """Test that /branding returns configured logo_url."""
        monkeypatch.setenv('LOGO_URL', 'https://example.com/logo.png')
        from core.config import get_settings
        get_settings.cache_clear()

        from api.main import create_app
        app = create_app()
        client = TestClient(app)

        response = client.get('/branding')
        data = response.json()
        assert data['logo_url'] == 'https://example.com/logo.png'

    def test_branding_endpoint_returns_primary_color(self, clean_env, monkeypatch):
        """Test that /branding returns configured primary_color."""
        monkeypatch.setenv('PRIMARY_COLOR', '#FF0000')
        from core.config import get_settings
        get_settings.cache_clear()

        from api.main import create_app
        app = create_app()
        client = TestClient(app)

        response = client.get('/branding')
        data = response.json()
        assert data['primary_color'] == '#FF0000'

    def test_branding_endpoint_default_values(self, clean_env):
        """Test that /branding returns default values when not configured."""
        from core.config import get_settings
        get_settings.cache_clear()

        from api.main import create_app
        app = create_app()
        client = TestClient(app)

        response = client.get('/branding')
        data = response.json()

        assert data['app_name'] == 'Helix'
        assert data['bot_name'] == 'Helix Assistant'
        assert data['primary_color'] == '#3B82F6'
