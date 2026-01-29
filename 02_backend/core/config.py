"""
Centralized configuration module for Helix.

All client-specific values are loaded from environment variables,
enabling white-label deployment without code changes.

Required Environment Variables:
    - APP_NAME: Application name (no default)
    - BOT_NAME: Bot persona name (no default)
    - DATABASE_URL: PostgreSQL connection string (no default)

Optional Environment Variables:
    - LOGO_URL: URL to logo image (default: None)
    - PRIMARY_COLOR: Brand color hex (default: #3B82F6)
    - APP_DESCRIPTION: Short description (default: 'AI-powered Q&A chatbot')
    - REDIS_URL: Redis connection (default: redis://localhost:6379)
    - And many more (see .env.example)

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


class SecretsConfig(BaseModel):
    """Secrets configuration for API keys and tokens.

    This class holds all sensitive configuration that should never
    be exposed to the frontend or logged.

    Attributes:
        openai_api_key: OpenAI API key for LLM generation.
        anthropic_api_key: Anthropic API key for fallback LLM.
        google_translate_api_key: Google Translate API key.
        fb_page_access_token: Facebook page access token.
        fb_verify_token: Facebook webhook verification token.
        fb_app_secret: Facebook app secret for signature validation.
        api_key: Admin API key for backend endpoints.
        secret_key: Secret key for signing tokens.
    """

    # LLM Provider Keys
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None

    # Translation
    google_translate_api_key: Optional[str] = None

    # Facebook Messenger
    fb_page_access_token: Optional[str] = None
    fb_verify_token: Optional[str] = None
    fb_app_secret: Optional[str] = None

    # Security
    api_key: Optional[str] = None
    secret_key: str = 'dev-secret-key-change-in-production'


class BrandingConfig(BaseModel):
    """Branding configuration for white-label deployment.

    Attributes:
        app_name: Application name displayed in UI and API docs (REQUIRED).
        app_description: Short description for API documentation.
        bot_name: Name used by the chatbot when responding (REQUIRED).
        logo_url: URL to logo image (optional).
        primary_color: Primary brand color in hex format.
    """

    app_name: str  # Required, no default
    app_description: str = 'AI-powered Q&A chatbot'
    bot_name: str  # Required, no default
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

    Security Note:
        Secrets (API keys, tokens) are isolated in the `secrets` attribute
        and should never be exposed to the frontend or logged.

    Attributes:
        database_url: PostgreSQL connection string.
        redis_url: Redis connection string for caching.
        secrets: Sensitive configuration (API keys, tokens).
        debug: Enable debug mode.
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR).
        cors_origins: Allowed CORS origins.
        branding: White-label branding configuration (public-safe).
        features: Feature flags for enabling/disabling functionality.
    """

    # Database (set via environment, empty string as fallback for testing)
    database_url: str = ''

    # Redis
    redis_url: str = 'redis://localhost:6379'

    # Secrets (API keys, tokens, credentials)
    secrets: SecretsConfig = SecretsConfig()

    # Debug
    debug: bool = False
    log_level: str = 'INFO'

    # CORS
    cors_origins: list[str] = ['http://localhost:3000', 'http://localhost:5173']

    # Branding (required fields must be set via environment)
    branding: BrandingConfig

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

        # Secrets
        secrets_data = self._load_secrets_from_env()
        if secrets_data:
            data['secrets'] = SecretsConfig(**secrets_data)

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
        """Load branding configuration from environment.

        Raises:
            ValueError: If required branding config is missing.
        """
        branding_data: dict = {}

        # Required fields
        app_name = os.getenv('APP_NAME')
        if not app_name:
            raise ValueError(
                "APP_NAME is required. Please set the APP_NAME environment variable."
            )
        branding_data['app_name'] = app_name

        bot_name = os.getenv('BOT_NAME')
        if not bot_name:
            raise ValueError(
                "BOT_NAME is required. Please set the BOT_NAME environment variable."
            )
        branding_data['bot_name'] = bot_name

        # Optional fields
        if os.getenv('APP_DESCRIPTION'):
            branding_data['app_description'] = os.getenv('APP_DESCRIPTION')
        if os.getenv('LOGO_URL'):
            branding_data['logo_url'] = os.getenv('LOGO_URL')
        if os.getenv('PRIMARY_COLOR'):
            branding_data['primary_color'] = os.getenv('PRIMARY_COLOR')

        return branding_data

    def _load_secrets_from_env(self) -> dict:
        """Load secrets configuration from environment.

        Returns:
            Dictionary of secrets loaded from environment.
        """
        secrets_data: dict = {}

        # LLM Provider Keys
        if os.getenv('OPENAI_API_KEY'):
            secrets_data['openai_api_key'] = os.getenv('OPENAI_API_KEY')
        if os.getenv('ANTHROPIC_API_KEY'):
            secrets_data['anthropic_api_key'] = os.getenv('ANTHROPIC_API_KEY')

        # Translation
        if os.getenv('GOOGLE_TRANSLATE_API_KEY'):
            secrets_data['google_translate_api_key'] = os.getenv('GOOGLE_TRANSLATE_API_KEY')

        # Facebook Messenger
        if os.getenv('FB_PAGE_ACCESS_TOKEN'):
            secrets_data['fb_page_access_token'] = os.getenv('FB_PAGE_ACCESS_TOKEN')
        if os.getenv('FB_VERIFY_TOKEN'):
            secrets_data['fb_verify_token'] = os.getenv('FB_VERIFY_TOKEN')
        if os.getenv('FB_APP_SECRET'):
            secrets_data['fb_app_secret'] = os.getenv('FB_APP_SECRET')

        # Security
        if os.getenv('API_KEY'):
            secrets_data['api_key'] = os.getenv('API_KEY')
        if os.getenv('SECRET_KEY'):
            secrets_data['secret_key'] = os.getenv('SECRET_KEY')

        return secrets_data

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


def validate_config(settings: Settings) -> None:
    """Validate that all required configuration is present.

    This function should be called at application startup to fail fast
    if required configuration is missing.

    Args:
        settings: Settings instance to validate.

    Raises:
        ValueError: If any required configuration is missing.
    """
    missing_fields = []

    # Check required database URL
    if not settings.database_url or settings.database_url.strip() == '':
        missing_fields.append('DATABASE_URL')

    if missing_fields:
        fields_list = ', '.join(missing_fields)
        raise ValueError(
            f"Missing required configuration: {fields_list}. "
            f"Please set the following environment variables: {fields_list}"
        )


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance.

    Returns:
        Cached Settings instance loaded from environment.
    """
    return Settings()
