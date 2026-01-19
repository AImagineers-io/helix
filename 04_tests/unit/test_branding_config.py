"""
Unit tests for branding configuration.

Tests cover:
- APP_NAME configuration
- APP_DESCRIPTION configuration
- BOT_NAME configuration
- LOGO_URL configuration
- PRIMARY_COLOR configuration
- Default values for white-label deployment
"""
import pytest
from core.config import Settings, BrandingConfig, get_settings


class TestBrandingConfig:
    """Tests for branding configuration settings."""

    def test_app_name_default(self, clean_env):
        """Test that APP_NAME defaults to 'Helix'."""
        settings = Settings()
        assert settings.branding.app_name == 'Helix'

    def test_app_name_from_env(self, clean_env, monkeypatch):
        """Test that APP_NAME is loaded from environment."""
        monkeypatch.setenv('APP_NAME', 'Custom Bot')
        settings = Settings()
        assert settings.branding.app_name == 'Custom Bot'

    def test_app_description_default(self, clean_env):
        """Test that APP_DESCRIPTION has sensible default."""
        settings = Settings()
        assert settings.branding.app_description == 'AI-powered Q&A chatbot'

    def test_app_description_from_env(self, clean_env, monkeypatch):
        """Test that APP_DESCRIPTION is loaded from environment."""
        monkeypatch.setenv('APP_DESCRIPTION', 'Custom AI assistant for your business')
        settings = Settings()
        assert settings.branding.app_description == 'Custom AI assistant for your business'

    def test_bot_name_default(self, clean_env):
        """Test that BOT_NAME defaults to 'Helix Assistant'."""
        settings = Settings()
        assert settings.branding.bot_name == 'Helix Assistant'

    def test_bot_name_from_env(self, clean_env, monkeypatch):
        """Test that BOT_NAME is loaded from environment."""
        monkeypatch.setenv('BOT_NAME', 'Luna')
        settings = Settings()
        assert settings.branding.bot_name == 'Luna'

    def test_logo_url_default_none(self, clean_env):
        """Test that LOGO_URL defaults to None."""
        settings = Settings()
        assert settings.branding.logo_url is None

    def test_logo_url_from_env(self, clean_env, monkeypatch):
        """Test that LOGO_URL is loaded from environment."""
        monkeypatch.setenv('LOGO_URL', 'https://example.com/logo.png')
        settings = Settings()
        assert settings.branding.logo_url == 'https://example.com/logo.png'

    def test_primary_color_default(self, clean_env):
        """Test that PRIMARY_COLOR has sensible default."""
        settings = Settings()
        assert settings.branding.primary_color == '#3B82F6'  # Blue

    def test_primary_color_from_env(self, clean_env, monkeypatch):
        """Test that PRIMARY_COLOR is loaded from environment."""
        monkeypatch.setenv('PRIMARY_COLOR', '#FF5733')
        settings = Settings()
        assert settings.branding.primary_color == '#FF5733'


class TestBrandingConfigModel:
    """Tests for BrandingConfig as a separate model."""

    def test_branding_config_to_dict(self, clean_env, monkeypatch):
        """Test that branding config can be serialized to dict."""
        monkeypatch.setenv('APP_NAME', 'TestBot')
        monkeypatch.setenv('BOT_NAME', 'Test Assistant')
        settings = Settings()
        branding_dict = settings.branding.model_dump()

        assert branding_dict['app_name'] == 'TestBot'
        assert branding_dict['bot_name'] == 'Test Assistant'
        assert 'app_description' in branding_dict
        assert 'logo_url' in branding_dict
        assert 'primary_color' in branding_dict

    def test_branding_config_has_all_required_fields(self, clean_env):
        """Test that BrandingConfig exposes all required fields for frontend."""
        settings = Settings()
        branding = settings.branding

        # All these fields should be accessible
        assert hasattr(branding, 'app_name')
        assert hasattr(branding, 'app_description')
        assert hasattr(branding, 'bot_name')
        assert hasattr(branding, 'logo_url')
        assert hasattr(branding, 'primary_color')
