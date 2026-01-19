"""
Branding API router.

Returns current instance branding configuration for frontend use.
This endpoint allows frontends to dynamically load branding without
requiring separate builds for each client instance.
"""
from typing import Dict, Any

from fastapi import APIRouter

from core.config import get_settings

router = APIRouter()


@router.get('/branding')
def get_branding() -> Dict[str, Any]:
    """Return current instance branding configuration.

    Returns branding settings for the current instance including:
    - app_name: Application display name
    - app_description: Short description
    - bot_name: Chatbot persona name
    - logo_url: URL to logo image (may be null)
    - primary_color: Brand color in hex format

    Returns:
        dict: Branding configuration for frontend consumption.
    """
    settings = get_settings()
    return settings.branding.model_dump()
