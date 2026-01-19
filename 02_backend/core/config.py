"""
Centralized configuration module for Helix.

All client-specific values are loaded from environment variables,
enabling white-label deployment without code changes.

Usage:
    from core.config import get_settings

    settings = get_settings()
    print(settings.branding.app_name)
    print(settings.features.is_enabled('analytics'))
"""
import os
from functools import lru_cache
from typing import Optional
from pydantic import BaseModel


def _parse_bool(value: str) -> bool:
    """Parse boolean value from string."""
    return value.lower() in ('true', '1', 'yes')


class BrandingConfig(BaseModel):
    """Branding configuration for white-label deployment.

    Attributes:
        app_name: Application name displayed in UI and API docs.
        app_description: Short description for API documentation.
        bot_name: Name used by the chatbot when responding.
        logo_url: URL to logo image (optional).
        primary_color: Primary brand color in hex format.
    """

    app_name: str = 'Helix'
    app_description: str = 'AI-powered Q&A chatbot'
    bot_name: str = 'Helix Assistant'
    logo_url: Optional[str] = None
    primary_color: str = '#3B82F6'


class FeatureFlags(BaseModel):
    """Feature flags to enable/disable functionality.

    Attributes:
        enable_variety_processor: Enable variety-specific chat processing.
        enable_messenger: Enable Facebook Messenger integration.
        enable_analytics: Enable analytics and observability features.
    """

    enable_variety_processor: bool = True
    enable_messenger: bool = True
    enable_analytics: bool = True

    def is_enabled(self, feature_name: str) -> bool:
        """Check if a feature is enabled by name.

        Args:
            feature_name: Feature name without 'enable_' prefix.

        Returns:
            True if feature is enabled, False otherwise.
        """
        attr_name = f'enable_{feature_name}'
        return getattr(self, attr_name, False)


class Settings(BaseModel):
    """Application settings loaded from environment.

    All settings can be overridden via environment variables.
    Settings are cached using get_settings() for performance.

    Attributes:
        database_url: PostgreSQL connection string.
        redis_url: Redis connection string for caching.
        secret_key: Secret key for signing tokens.
        api_key: API key for admin endpoints.
        debug: Enable debug mode.
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR).
        cors_origins: Allowed CORS origins.
        branding: White-label branding configuration.
        features: Feature flags for enabling/disabling functionality.
    """

    # Database
    database_url: str = ''

    # Redis
    redis_url: str = 'redis://localhost:6379'

    # Security
    secret_key: str = 'dev-secret-key-change-in-production'
    api_key: Optional[str] = None

    # Debug
    debug: bool = False
    log_level: str = 'INFO'

    # CORS
    cors_origins: list[str] = ['http://localhost:3000', 'http://localhost:5173']

    # Branding
    branding: BrandingConfig = BrandingConfig()

    # Feature flags
    features: FeatureFlags = FeatureFlags()

    def __init__(self, **data):
        """Initialize settings, loading from environment first."""
        env_data = self._load_from_env()
        env_data.update(data)
        super().__init__(**env_data)

    def _load_from_env(self) -> dict:
        """Load settings from environment variables.

        Returns:
            Dictionary of settings loaded from environment.
        """
        data: dict = {}

        # Core settings
        if os.getenv('DATABASE_URL'):
            data['database_url'] = os.getenv('DATABASE_URL')
        if os.getenv('REDIS_URL'):
            data['redis_url'] = os.getenv('REDIS_URL')
        if os.getenv('SECRET_KEY'):
            data['secret_key'] = os.getenv('SECRET_KEY')
        if os.getenv('API_KEY'):
            data['api_key'] = os.getenv('API_KEY')

        # Debug settings
        data['debug'] = _parse_bool(os.getenv('DEBUG', 'false'))
        if os.getenv('LOG_LEVEL'):
            data['log_level'] = os.getenv('LOG_LEVEL')

        # CORS
        cors_str = os.getenv('CORS_ORIGINS')
        if cors_str:
            data['cors_origins'] = [o.strip() for o in cors_str.split(',')]

        # Branding
        branding_data = self._load_branding_from_env()
        if branding_data:
            data['branding'] = BrandingConfig(**branding_data)

        # Feature flags
        features_data = self._load_features_from_env()
        if features_data:
            data['features'] = FeatureFlags(**features_data)

        return data

    def _load_branding_from_env(self) -> dict:
        """Load branding configuration from environment."""
        branding_data: dict = {}
        if os.getenv('APP_NAME'):
            branding_data['app_name'] = os.getenv('APP_NAME')
        if os.getenv('APP_DESCRIPTION'):
            branding_data['app_description'] = os.getenv('APP_DESCRIPTION')
        if os.getenv('BOT_NAME'):
            branding_data['bot_name'] = os.getenv('BOT_NAME')
        if os.getenv('LOGO_URL'):
            branding_data['logo_url'] = os.getenv('LOGO_URL')
        if os.getenv('PRIMARY_COLOR'):
            branding_data['primary_color'] = os.getenv('PRIMARY_COLOR')
        return branding_data

    def _load_features_from_env(self) -> dict:
        """Load feature flags from environment."""
        features_data: dict = {}
        if os.getenv('ENABLE_VARIETY_PROCESSOR'):
            features_data['enable_variety_processor'] = _parse_bool(
                os.getenv('ENABLE_VARIETY_PROCESSOR', 'true')
            )
        if os.getenv('ENABLE_MESSENGER'):
            features_data['enable_messenger'] = _parse_bool(
                os.getenv('ENABLE_MESSENGER', 'true')
            )
        if os.getenv('ENABLE_ANALYTICS'):
            features_data['enable_analytics'] = _parse_bool(
                os.getenv('ENABLE_ANALYTICS', 'true')
            )
        return features_data


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance.

    Returns:
        Cached Settings instance loaded from environment.
    """
    return Settings()
