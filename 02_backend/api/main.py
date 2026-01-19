"""
FastAPI application entry point for Helix.

The application uses centralized configuration for white-label deployment.
All branding and feature configuration is loaded from environment variables.

Usage:
    uvicorn api.main:app --reload

Environment Variables:
    See .env.example for all configuration options.
"""
import json
from pathlib import Path
from typing import Dict, Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import get_settings, Settings
from api.routers import branding, prompts


def get_version() -> str:
    """Load version from version.json.

    Returns:
        Version string from version.json or '0.1.0' as fallback.
    """
    version_file = Path(__file__).parent.parent.parent.parent / 'version.json'
    try:
        with open(version_file, 'r') as f:
            version_info = json.load(f)
            return version_info.get('version', '0.1.0')
    except Exception:
        return '0.1.0'


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create and configure the FastAPI application.

    Args:
        settings: Optional settings instance. If not provided, loads from env.

    Returns:
        Configured FastAPI application instance.
    """
    if settings is None:
        settings = get_settings()

    app = FastAPI(
        title=settings.branding.app_name,
        description=settings.branding.app_description,
        version=get_version(),
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=['*'],
        allow_headers=['*'],
    )

    # Include routers
    app.include_router(branding.router, tags=['Branding'])
    app.include_router(prompts.router)

    # Health endpoint
    @app.get('/health', tags=['System'])
    def health_check() -> Dict[str, Any]:
        """Health check endpoint for monitoring.

        Returns:
            Health status including app name and version.
        """
        return {
            'status': 'ok',
            'app_name': settings.branding.app_name,
            'version': get_version(),
        }

    return app


# Create default app instance for uvicorn
app = create_app()
