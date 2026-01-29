"""
Tests for config defaults validation.

Tests that required config fields are properly enforced and optional
config fields have sensible defaults.
"""
import os
import pytest
from core.config import Settings, BrandingConfig


class TestConfigDefaults:
    """Test suite for config defaults and required fields."""

    def test_branding_config_has_required_fields(self):
        """Test that BrandingConfig requires APP_NAME and BOT_NAME."""
        # Arrange: Clear environment to test defaults
        env_backup = {}
        for key in ['APP_NAME', 'BOT_NAME', 'LOGO_URL', 'PRIMARY_COLOR']:
            env_backup[key] = os.environ.pop(key, None)

        try:
            # Act & Assert: Should fail when required fields missing
            with pytest.raises(ValueError, match="APP_NAME is required"):
                Settings()
        finally:
            # Restore environment
            for key, value in env_backup.items():
                if value is not None:
                    os.environ[key] = value

    def test_branding_config_app_name_from_env(self):
        """Test that APP_NAME is loaded from environment."""
        # Arrange
        os.environ['APP_NAME'] = 'TestApp'
        os.environ['BOT_NAME'] = 'TestBot'

        try:
            # Act
            settings = Settings()

            # Assert
            assert settings.branding.app_name == 'TestApp'
        finally:
            # Cleanup
            os.environ.pop('APP_NAME', None)
            os.environ.pop('BOT_NAME', None)

    def test_branding_config_bot_name_from_env(self):
        """Test that BOT_NAME is loaded from environment."""
        # Arrange
        os.environ['APP_NAME'] = 'TestApp'
        os.environ['BOT_NAME'] = 'TestBot'

        try:
            # Act
            settings = Settings()

            # Assert
            assert settings.branding.bot_name == 'TestBot'
        finally:
            # Cleanup
            os.environ.pop('APP_NAME', None)
            os.environ.pop('BOT_NAME', None)

    def test_branding_config_optional_logo_url_defaults_to_none(self):
        """Test that LOGO_URL is optional and defaults to None."""
        # Arrange
        os.environ['APP_NAME'] = 'TestApp'
        os.environ['BOT_NAME'] = 'TestBot'

        try:
            # Act
            settings = Settings()

            # Assert
            assert settings.branding.logo_url is None
        finally:
            # Cleanup
            os.environ.pop('APP_NAME', None)
            os.environ.pop('BOT_NAME', None)

    def test_branding_config_optional_primary_color_has_default(self):
        """Test that PRIMARY_COLOR is optional with default value."""
        # Arrange
        os.environ['APP_NAME'] = 'TestApp'
        os.environ['BOT_NAME'] = 'TestBot'

        try:
            # Act
            settings = Settings()

            # Assert
            assert settings.branding.primary_color == '#3B82F6'
        finally:
            # Cleanup
            os.environ.pop('APP_NAME', None)
            os.environ.pop('BOT_NAME', None)

    def test_branding_config_app_description_has_default(self):
        """Test that APP_DESCRIPTION is optional with default value."""
        # Arrange
        os.environ['APP_NAME'] = 'TestApp'
        os.environ['BOT_NAME'] = 'TestBot'

        try:
            # Act
            settings = Settings()

            # Assert
            assert settings.branding.app_description == 'AI-powered Q&A chatbot'
        finally:
            # Cleanup
            os.environ.pop('APP_NAME', None)
            os.environ.pop('BOT_NAME', None)

    def test_branding_config_logo_url_can_be_set(self):
        """Test that LOGO_URL can be set from environment."""
        # Arrange
        os.environ['APP_NAME'] = 'TestApp'
        os.environ['BOT_NAME'] = 'TestBot'
        os.environ['LOGO_URL'] = 'https://example.com/logo.png'

        try:
            # Act
            settings = Settings()

            # Assert
            assert settings.branding.logo_url == 'https://example.com/logo.png'
        finally:
            # Cleanup
            os.environ.pop('APP_NAME', None)
            os.environ.pop('BOT_NAME', None)
            os.environ.pop('LOGO_URL', None)

    def test_branding_config_primary_color_can_be_customized(self):
        """Test that PRIMARY_COLOR can be customized from environment."""
        # Arrange
        os.environ['APP_NAME'] = 'TestApp'
        os.environ['BOT_NAME'] = 'TestBot'
        os.environ['PRIMARY_COLOR'] = '#FF5733'

        try:
            # Act
            settings = Settings()

            # Assert
            assert settings.branding.primary_color == '#FF5733'
        finally:
            # Cleanup
            os.environ.pop('APP_NAME', None)
            os.environ.pop('BOT_NAME', None)
            os.environ.pop('PRIMARY_COLOR', None)
