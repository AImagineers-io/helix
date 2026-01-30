"""
Shared test fixtures for Helix tests.
"""
import os
import sys
import pytest

# Add backend to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '02_backend'))
# Add scripts to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


# Set default environment variables for testing
# These are required by the application config
os.environ.setdefault('APP_NAME', 'Helix Test')
os.environ.setdefault('BOT_NAME', 'Test Bot')
os.environ.setdefault('DATABASE_URL', 'sqlite:///:memory:')


@pytest.fixture
def test_client():
    """Create a test client for API testing."""
    from fastapi.testclient import TestClient
    from api.main import create_app

    app = create_app()
    return TestClient(app)


@pytest.fixture
def db_session():
    """Create a database session for testing."""
    # Skip if no real database configured
    pytest.skip("Database session requires configured database")


@pytest.fixture
def clean_env(monkeypatch):
    """Fixture to provide a clean environment for config tests.

    Sets required branding env vars to test values.
    """
    # Clear all config-related env vars first
    env_vars_to_clear = [
        'DATABASE_URL', 'REDIS_URL', 'SECRET_KEY', 'API_KEY', 'DEBUG', 'LOG_LEVEL',
        'CORS_ORIGINS', 'APP_NAME', 'APP_DESCRIPTION', 'BOT_NAME', 'LOGO_URL',
        'PRIMARY_COLOR', 'ENABLE_MESSENGER',
        'ENABLE_ANALYTICS', 'OPENAI_API_KEY', 'ANTHROPIC_API_KEY'
    ]
    for var in env_vars_to_clear:
        monkeypatch.delenv(var, raising=False)

    # Set required env vars for config to work
    monkeypatch.setenv('APP_NAME', 'Helix Test')
    monkeypatch.setenv('BOT_NAME', 'Test Bot')

    return monkeypatch
