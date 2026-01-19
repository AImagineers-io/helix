"""
Unit tests for centralized configuration module.

Tests cover:
- Core settings (database, redis, security)
- Default values when env vars not set
- Validation of required settings
- Environment variable loading
"""
import pytest
from core.config import Settings, get_settings


class TestCoreSettings:
    """Tests for core application settings."""

    def test_settings_loads_database_url_from_env(self, clean_env, monkeypatch):
        """Test that DATABASE_URL is loaded from environment."""
        monkeypatch.setenv('DATABASE_URL', 'postgresql://user:pass@localhost:5432/testdb')
        settings = Settings()
        assert settings.database_url == 'postgresql://user:pass@localhost:5432/testdb'

    def test_settings_loads_redis_url_from_env(self, clean_env, monkeypatch):
        """Test that REDIS_URL is loaded from environment."""
        monkeypatch.setenv('REDIS_URL', 'redis://localhost:6379')
        settings = Settings()
        assert settings.redis_url == 'redis://localhost:6379'

    def test_settings_redis_url_default(self, clean_env):
        """Test that REDIS_URL has sensible default."""
        settings = Settings()
        assert settings.redis_url == 'redis://localhost:6379'

    def test_settings_loads_secret_key_from_env(self, clean_env, monkeypatch):
        """Test that SECRET_KEY is loaded from environment."""
        monkeypatch.setenv('SECRET_KEY', 'my-secret-key-123')
        settings = Settings()
        assert settings.secret_key == 'my-secret-key-123'

    def test_settings_secret_key_default(self, clean_env):
        """Test that SECRET_KEY has a default for development."""
        settings = Settings()
        assert settings.secret_key == 'dev-secret-key-change-in-production'

    def test_settings_loads_api_key_from_env(self, clean_env, monkeypatch):
        """Test that API_KEY is loaded from environment."""
        monkeypatch.setenv('API_KEY', 'admin-api-key-456')
        settings = Settings()
        assert settings.api_key == 'admin-api-key-456'

    def test_settings_debug_default_false(self, clean_env):
        """Test that DEBUG defaults to False for safety."""
        settings = Settings()
        assert settings.debug is False

    def test_settings_debug_true_from_env(self, clean_env, monkeypatch):
        """Test that DEBUG can be enabled via environment."""
        monkeypatch.setenv('DEBUG', 'true')
        settings = Settings()
        assert settings.debug is True

    def test_settings_log_level_default(self, clean_env):
        """Test that LOG_LEVEL defaults to INFO."""
        settings = Settings()
        assert settings.log_level == 'INFO'

    def test_settings_log_level_from_env(self, clean_env, monkeypatch):
        """Test that LOG_LEVEL is loaded from environment."""
        monkeypatch.setenv('LOG_LEVEL', 'DEBUG')
        settings = Settings()
        assert settings.log_level == 'DEBUG'

    def test_settings_cors_origins_default(self, clean_env):
        """Test that CORS_ORIGINS has sensible default."""
        settings = Settings()
        assert 'http://localhost:3000' in settings.cors_origins

    def test_settings_cors_origins_from_env(self, clean_env, monkeypatch):
        """Test that CORS_ORIGINS is loaded as list from comma-separated env."""
        monkeypatch.setenv('CORS_ORIGINS', 'https://example.com,https://app.example.com')
        settings = Settings()
        assert settings.cors_origins == ['https://example.com', 'https://app.example.com']


class TestSingletonSettings:
    """Tests for settings singleton pattern."""

    def test_get_settings_returns_settings_instance(self, clean_env):
        """Test that get_settings returns a Settings instance."""
        settings = get_settings()
        assert isinstance(settings, Settings)

    def test_get_settings_is_cached(self, clean_env):
        """Test that get_settings returns cached instance."""
        # Clear any cached settings first
        get_settings.cache_clear()
        settings1 = get_settings()
        settings2 = get_settings()
        assert settings1 is settings2
