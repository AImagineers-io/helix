"""
Shared test fixtures for Helix tests.
"""
import os
import sys
import pytest

# Add backend to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '02_backend'))


@pytest.fixture
def clean_env(monkeypatch):
    """Fixture to provide a clean environment for config tests."""
    # Clear all config-related env vars
    env_vars_to_clear = [
        'DATABASE_URL', 'REDIS_URL', 'SECRET_KEY', 'API_KEY', 'DEBUG', 'LOG_LEVEL',
        'CORS_ORIGINS', 'APP_NAME', 'APP_DESCRIPTION', 'BOT_NAME', 'LOGO_URL',
        'PRIMARY_COLOR', 'ENABLE_VARIETY_PROCESSOR', 'ENABLE_MESSENGER',
        'ENABLE_ANALYTICS', 'OPENAI_API_KEY', 'ANTHROPIC_API_KEY'
    ]
    for var in env_vars_to_clear:
        monkeypatch.delenv(var, raising=False)
    return monkeypatch
