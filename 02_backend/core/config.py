"""
Centralized configuration module for Helix.

All client-specific values are loaded from environment variables,
enabling white-label deployment without code changes.

Required Environment Variables:
    - APP_NAME: Application name (no default)
    - BOT_NAME: Bot persona name (no default)
    - DATABASE_URL: PostgreSQL connection string (no default)

Optional Environment Variables:
    - ENVIRONMENT: Environment type (development, demo, production)
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
import re
from functools import lru_cache
from typing import Literal, Optional
from urllib.parse import urlparse
from pydantic import BaseModel


# Environment type constants
ENV_DEVELOPMENT = 'development'
ENV_DEMO = 'demo'
ENV_PRODUCTION = 'production'

# Pre-compiled regex for production database detection
_PRODUCTION_DB_PATTERN = re.compile(r'prod', re.IGNORECASE)


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
        enable_messenger: Enable Facebook Messenger integration.
        enable_analytics: Enable analytics and observability features.
    """

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


class DemoAuthConfig(BaseModel):
    """Demo environment authentication configuration.

    Provides basic HTTP authentication for demo environments to prevent
    unauthorized access while keeping authentication simple for demos.

    Attributes:
        enabled: Whether demo auth is enabled (requires username and password).
        username: Username for basic auth.
        password: Password for basic auth.
        public_paths: Paths that don't require authentication.
    """

    enabled: bool = False
    username: Optional[str] = None
    password: Optional[str] = None
    public_paths: list[str] = ['/health', '/branding', '/docs', '/openapi.json']

    def __init__(self, **data):
        """Initialize and auto-enable if credentials are set."""
        super().__init__(**data)
        if self.username and self.password:
            object.__setattr__(self, 'enabled', True)


class Settings(BaseModel):
    """Application settings loaded from environment.

    All settings can be overridden via environment variables.
    Settings are cached using get_settings() for performance.

    Security Note:
        Secrets (API keys, tokens) are isolated in the `secrets` attribute
        and should never be exposed to the frontend or logged.

    Attributes:
        environment: Deployment environment (development, demo, production).
        database_url: PostgreSQL connection string.
        redis_url: Redis connection string for caching.
        secrets: Sensitive configuration (API keys, tokens).
        debug: Enable debug mode.
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR).
        cors_origins: Allowed CORS origins.
        branding: White-label branding configuration (public-safe).
        features: Feature flags for enabling/disabling functionality.
    """

    # Environment (development, demo, production)
    environment: str = 'development'

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

    # Demo environment authentication
    demo_auth: DemoAuthConfig = DemoAuthConfig()

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

        # Environment
        data['environment'] = os.getenv('ENVIRONMENT', 'development')

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

        # Demo auth
        demo_auth_data = self._load_demo_auth_from_env()
        if demo_auth_data:
            data['demo_auth'] = DemoAuthConfig(**demo_auth_data)

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
        if os.getenv('ENABLE_MESSENGER'):
            features_data['enable_messenger'] = _parse_bool(
                os.getenv('ENABLE_MESSENGER', 'true')
            )
        if os.getenv('ENABLE_ANALYTICS'):
            features_data['enable_analytics'] = _parse_bool(
                os.getenv('ENABLE_ANALYTICS', 'true')
            )
        return features_data

    def _load_demo_auth_from_env(self) -> dict:
        """Load demo authentication configuration from environment.

        Returns:
            Dictionary of demo auth config loaded from environment.
        """
        demo_auth_data: dict = {}

        if os.getenv('DEMO_USERNAME'):
            demo_auth_data['username'] = os.getenv('DEMO_USERNAME')
        if os.getenv('DEMO_PASSWORD'):
            demo_auth_data['password'] = os.getenv('DEMO_PASSWORD')
        if os.getenv('DEMO_PUBLIC_PATHS'):
            demo_auth_data['public_paths'] = [
                p.strip() for p in os.getenv('DEMO_PUBLIC_PATHS', '').split(',')
            ]

        return demo_auth_data


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


def is_production_database_url(database_url: str) -> bool:
    """Check if a database URL appears to be a production database.

    Identifies production databases by looking for 'prod' in:
    - The hostname
    - The database name

    Args:
        database_url: Database connection string.

    Returns:
        True if the URL appears to be a production database.

    Examples:
        >>> is_production_database_url('postgresql://u:p@prod-db.com:5432/db')
        True
        >>> is_production_database_url('postgresql://u:p@localhost:5432/helix')
        False
        >>> is_production_database_url('sqlite:///:memory:')
        False
    """
    if not database_url:
        return False

    # SQLite databases are never considered production
    if database_url.startswith('sqlite://'):
        return False

    try:
        parsed = urlparse(database_url)
        hostname = parsed.hostname or ''
        db_name = (parsed.path or '').lstrip('/')

        return bool(
            _PRODUCTION_DB_PATTERN.search(hostname) or
            _PRODUCTION_DB_PATTERN.search(db_name)
        )
    except Exception:
        return False


def validate_environment_safety(settings: Settings) -> None:
    """Validate that demo environments cannot connect to production databases.

    This is a critical safety check to prevent demo environments from
    accidentally accessing or modifying production data.

    Call this function at application startup to fail fast if the demo
    environment is misconfigured.

    Args:
        settings: Settings instance to validate.

    Raises:
        ValueError: If demo environment is configured with production database.
    """
    if settings.environment != ENV_DEMO:
        return

    if is_production_database_url(settings.database_url):
        raise ValueError(
            "Demo environment cannot connect to production database. "
            f"DATABASE_URL appears to be a production database: {settings.database_url}. "
            "Please use a demo or development database URL."
        )
