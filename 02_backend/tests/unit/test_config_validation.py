"""
Tests for config validation at startup.

Tests that the application fails fast with clear error messages when
required configuration is missing at startup.
"""
import os
import pytest
from core.config import Settings, validate_config


class TestConfigValidation:
    """Test suite for startup config validation."""

    def test_validate_config_passes_with_all_required_fields(self):
        """Test that validation passes when all required fields are set."""
        # Arrange
        os.environ['APP_NAME'] = 'TestApp'
        os.environ['BOT_NAME'] = 'TestBot'
        os.environ['DATABASE_URL'] = 'postgresql://localhost/test'

        try:
            # Act & Assert
            settings = Settings()
            validate_config(settings)  # Should not raise
        finally:
            # Cleanup
            os.environ.pop('APP_NAME', None)
            os.environ.pop('BOT_NAME', None)
            os.environ.pop('DATABASE_URL', None)

    def test_validate_config_fails_when_app_name_missing(self):
        """Test that validation fails with clear message when APP_NAME missing."""
        # Arrange: Don't set APP_NAME
        os.environ.pop('APP_NAME', None)

        # Act & Assert
        with pytest.raises(ValueError, match="APP_NAME"):
            Settings()

    def test_validate_config_fails_when_bot_name_missing(self):
        """Test that validation fails with clear message when BOT_NAME missing."""
        # Arrange
        os.environ['APP_NAME'] = 'TestApp'
        os.environ.pop('BOT_NAME', None)

        try:
            # Act & Assert
            with pytest.raises(ValueError, match="BOT_NAME"):
                Settings()
        finally:
            os.environ.pop('APP_NAME', None)

    def test_validate_config_fails_when_database_url_missing(self):
        """Test that validation fails when DATABASE_URL is missing."""
        # Arrange
        os.environ['APP_NAME'] = 'TestApp'
        os.environ['BOT_NAME'] = 'TestBot'
        os.environ.pop('DATABASE_URL', None)

        try:
            # Act
            settings = Settings()

            # Assert
            with pytest.raises(ValueError, match="DATABASE_URL"):
                validate_config(settings)
        finally:
            os.environ.pop('APP_NAME', None)
            os.environ.pop('BOT_NAME', None)

    def test_validate_config_fails_when_database_url_empty(self):
        """Test that validation fails when DATABASE_URL is empty string."""
        # Arrange
        os.environ['APP_NAME'] = 'TestApp'
        os.environ['BOT_NAME'] = 'TestBot'
        os.environ['DATABASE_URL'] = ''

        try:
            # Act
            settings = Settings()

            # Assert
            with pytest.raises(ValueError, match="DATABASE_URL"):
                validate_config(settings)
        finally:
            os.environ.pop('APP_NAME', None)
            os.environ.pop('BOT_NAME', None)
            os.environ.pop('DATABASE_URL', None)

    def test_validate_config_lists_all_missing_fields(self):
        """Test that validation error lists all missing required fields."""
        # Arrange
        os.environ['APP_NAME'] = 'TestApp'
        os.environ['BOT_NAME'] = 'TestBot'
        os.environ.pop('DATABASE_URL', None)
        # Could add more missing fields here

        try:
            # Act
            settings = Settings()

            # Assert
            with pytest.raises(ValueError) as exc_info:
                validate_config(settings)

            error_message = str(exc_info.value)
            assert 'DATABASE_URL' in error_message
            assert 'required' in error_message.lower()
        finally:
            os.environ.pop('APP_NAME', None)
            os.environ.pop('BOT_NAME', None)

    def test_validate_config_provides_helpful_error_message(self):
        """Test that validation error includes helpful guidance."""
        # Arrange
        os.environ['APP_NAME'] = 'TestApp'
        os.environ['BOT_NAME'] = 'TestBot'
        os.environ.pop('DATABASE_URL', None)

        try:
            # Act
            settings = Settings()

            # Assert
            with pytest.raises(ValueError) as exc_info:
                validate_config(settings)

            error_message = str(exc_info.value)
            # Should mention setting environment variable
            assert 'environment variable' in error_message.lower() or 'env' in error_message.lower()
        finally:
            os.environ.pop('APP_NAME', None)
            os.environ.pop('BOT_NAME', None)
