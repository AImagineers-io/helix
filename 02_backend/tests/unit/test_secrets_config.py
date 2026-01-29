"""
Tests for secrets isolation from public config.

Tests that sensitive configuration (API keys, tokens) is properly
separated from public-safe branding configuration.
"""
import os
import pytest
from core.config import Settings, SecretsConfig, BrandingConfig


class TestSecretsIsolation:
    """Test suite for secrets isolation."""

    def test_secrets_config_class_exists(self):
        """Test that SecretsConfig class exists."""
        # Act & Assert
        assert SecretsConfig is not None

    def test_secrets_config_contains_api_keys(self):
        """Test that SecretsConfig contains API key fields."""
        # Arrange
        os.environ['APP_NAME'] = 'TestApp'
        os.environ['BOT_NAME'] = 'TestBot'
        os.environ['DATABASE_URL'] = 'postgresql://localhost/test'
        os.environ['OPENAI_API_KEY'] = 'sk-test'
        os.environ['ANTHROPIC_API_KEY'] = 'sk-ant-test'

        try:
            # Act
            settings = Settings()

            # Assert
            assert hasattr(settings, 'secrets')
            assert hasattr(settings.secrets, 'openai_api_key')
            assert hasattr(settings.secrets, 'anthropic_api_key')
            assert settings.secrets.openai_api_key == 'sk-test'
        finally:
            # Cleanup
            for key in ['APP_NAME', 'BOT_NAME', 'DATABASE_URL', 'OPENAI_API_KEY', 'ANTHROPIC_API_KEY']:
                os.environ.pop(key, None)

    def test_secrets_config_contains_facebook_credentials(self):
        """Test that SecretsConfig contains Facebook credentials."""
        # Arrange
        os.environ['APP_NAME'] = 'TestApp'
        os.environ['BOT_NAME'] = 'TestBot'
        os.environ['DATABASE_URL'] = 'postgresql://localhost/test'
        os.environ['FB_PAGE_ACCESS_TOKEN'] = 'fb-token'
        os.environ['FB_VERIFY_TOKEN'] = 'verify-token'
        os.environ['FB_APP_SECRET'] = 'app-secret'

        try:
            # Act
            settings = Settings()

            # Assert
            assert hasattr(settings.secrets, 'fb_page_access_token')
            assert hasattr(settings.secrets, 'fb_verify_token')
            assert hasattr(settings.secrets, 'fb_app_secret')
            assert settings.secrets.fb_page_access_token == 'fb-token'
        finally:
            # Cleanup
            for key in ['APP_NAME', 'BOT_NAME', 'DATABASE_URL', 'FB_PAGE_ACCESS_TOKEN', 'FB_VERIFY_TOKEN', 'FB_APP_SECRET']:
                os.environ.pop(key, None)

    def test_branding_config_does_not_contain_secrets(self):
        """Test that BrandingConfig does not expose sensitive data."""
        # Arrange
        os.environ['APP_NAME'] = 'TestApp'
        os.environ['BOT_NAME'] = 'TestBot'
        os.environ['DATABASE_URL'] = 'postgresql://localhost/test'
        os.environ['OPENAI_API_KEY'] = 'sk-test'
        os.environ['SECRET_KEY'] = 'secret-key'

        try:
            # Act
            settings = Settings()
            branding = settings.branding

            # Assert: Branding should not have any secret fields
            assert not hasattr(branding, 'openai_api_key')
            assert not hasattr(branding, 'secret_key')
            assert not hasattr(branding, 'api_key')
        finally:
            # Cleanup
            for key in ['APP_NAME', 'BOT_NAME', 'DATABASE_URL', 'OPENAI_API_KEY', 'SECRET_KEY']:
                os.environ.pop(key, None)

    def test_branding_config_model_dump_excludes_secrets(self):
        """Test that branding.model_dump() does not include secrets."""
        # Arrange
        os.environ['APP_NAME'] = 'TestApp'
        os.environ['BOT_NAME'] = 'TestBot'
        os.environ['DATABASE_URL'] = 'postgresql://localhost/test'
        os.environ['OPENAI_API_KEY'] = 'sk-test-secret'

        try:
            # Act
            settings = Settings()
            branding_dict = settings.branding.model_dump()

            # Assert: Serialized branding should not contain secrets
            branding_json = str(branding_dict)
            assert 'sk-test-secret' not in branding_json
            assert 'api_key' not in branding_json
            assert 'secret' not in branding_json.lower() or 'description' in branding_json.lower()  # Allow "description"
        finally:
            # Cleanup
            for key in ['APP_NAME', 'BOT_NAME', 'DATABASE_URL', 'OPENAI_API_KEY']:
                os.environ.pop(key, None)

    def test_secrets_config_has_optional_fields_with_defaults(self):
        """Test that SecretsConfig has optional fields with None defaults."""
        # Arrange
        os.environ['APP_NAME'] = 'TestApp'
        os.environ['BOT_NAME'] = 'TestBot'
        os.environ['DATABASE_URL'] = 'postgresql://localhost/test'
        # Don't set API keys

        try:
            # Act
            settings = Settings()

            # Assert: Missing secrets should be None, not raise errors
            assert settings.secrets.openai_api_key is None
            assert settings.secrets.anthropic_api_key is None
            assert settings.secrets.google_translate_api_key is None
        finally:
            # Cleanup
            for key in ['APP_NAME', 'BOT_NAME', 'DATABASE_URL']:
                os.environ.pop(key, None)

    def test_api_key_and_secret_key_in_secrets_config(self):
        """Test that API_KEY and SECRET_KEY are in SecretsConfig."""
        # Arrange
        os.environ['APP_NAME'] = 'TestApp'
        os.environ['BOT_NAME'] = 'TestBot'
        os.environ['DATABASE_URL'] = 'postgresql://localhost/test'
        os.environ['API_KEY'] = 'admin-api-key'
        os.environ['SECRET_KEY'] = 'jwt-secret'

        try:
            # Act
            settings = Settings()

            # Assert
            assert settings.secrets.api_key == 'admin-api-key'
            assert settings.secrets.secret_key == 'jwt-secret'
        finally:
            # Cleanup
            for key in ['APP_NAME', 'BOT_NAME', 'DATABASE_URL', 'API_KEY', 'SECRET_KEY']:
                os.environ.pop(key, None)
