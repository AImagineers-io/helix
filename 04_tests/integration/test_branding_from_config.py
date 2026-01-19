"""
Integration test to verify branding is loaded from configuration.

Tests that the application uses environment-based configuration
for all branding elements rather than hardcoded values.
"""
import os
import pytest
from fastapi.testclient import TestClient


def test_app_name_from_config():
    """Test that FastAPI app uses app_name from config."""
    # Set custom branding
    os.environ['APP_NAME'] = 'Test Chatbot'
    os.environ['APP_DESCRIPTION'] = 'Test Description'

    # Import after setting env vars
    from api.main import create_app
    from core.config import Settings

    # Clear settings cache
    from core.config import get_settings
    get_settings.cache_clear()

    settings = Settings()
    app = create_app(settings)

    assert app.title == 'Test Chatbot'
    assert app.description == 'Test Description'

    # Cleanup
    del os.environ['APP_NAME']
    del os.environ['APP_DESCRIPTION']
    get_settings.cache_clear()


def test_health_endpoint_returns_app_name():
    """Test that /health endpoint returns configured app name."""
    os.environ['APP_NAME'] = 'Custom Bot'

    from api.main import create_app
    from core.config import Settings, get_settings

    get_settings.cache_clear()
    settings = Settings()
    app = create_app(settings)

    client = TestClient(app)
    response = client.get('/health')

    assert response.status_code == 200
    data = response.json()
    assert data['app_name'] == 'Custom Bot'
    assert data['status'] == 'ok'

    # Cleanup
    del os.environ['APP_NAME']
    get_settings.cache_clear()


def test_branding_endpoint_returns_config():
    """Test that /branding endpoint returns all branding config."""
    os.environ['APP_NAME'] = 'My Bot'
    os.environ['BOT_NAME'] = 'My Assistant'
    os.environ['PRIMARY_COLOR'] = '#FF5733'

    from api.main import create_app
    from core.config import Settings, get_settings

    get_settings.cache_clear()
    settings = Settings()
    app = create_app(settings)

    client = TestClient(app)
    response = client.get('/branding')

    assert response.status_code == 200
    data = response.json()
    assert data['app_name'] == 'My Bot'
    assert data['bot_name'] == 'My Assistant'
    assert data['primary_color'] == '#FF5733'

    # Cleanup
    del os.environ['APP_NAME']
    del os.environ['BOT_NAME']
    del os.environ['PRIMARY_COLOR']
    get_settings.cache_clear()


def test_default_branding_is_helix():
    """Test that default branding (no env vars) uses Helix."""
    # Clear any existing env vars
    for key in ['APP_NAME', 'BOT_NAME', 'APP_DESCRIPTION']:
        if key in os.environ:
            del os.environ[key]

    from core.config import Settings, get_settings

    get_settings.cache_clear()
    settings = Settings()

    assert settings.branding.app_name == 'Helix'
    assert settings.branding.bot_name == 'Helix Assistant'
    assert 'Helix' in settings.branding.app_description or 'chatbot' in settings.branding.app_description.lower()

    get_settings.cache_clear()
