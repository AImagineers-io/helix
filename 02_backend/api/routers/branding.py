"""
Branding API router.

Returns current instance branding configuration for frontend use.
This endpoint allows frontends to dynamically load branding without
requiring separate builds for each client instance.

Caching Strategy:
- Cache-Control: public, max-age=3600 (1 hour)
- ETag for conditional requests (If-None-Match → 304 Not Modified)
"""
import hashlib
import json
from typing import Any

from fastapi import APIRouter, Request, Response

from core.config import get_settings

router = APIRouter()

# Cache TTL in seconds (1 hour)
CACHE_MAX_AGE = 3600


def _generate_etag(data: dict[str, Any]) -> str:
    """Generate ETag from branding data.

    Args:
        data: Branding configuration dictionary.

    Returns:
        ETag string in quoted format (e.g., '"abc123"').
    """
    content = json.dumps(data, sort_keys=True)
    hash_value = hashlib.md5(content.encode()).hexdigest()
    return f'"{hash_value}"'


def _set_cache_headers(response: Response, etag: str) -> None:
    """Set caching headers on response.

    Args:
        response: FastAPI Response object.
        etag: ETag value for the content.
    """
    response.headers['Cache-Control'] = f'public, max-age={CACHE_MAX_AGE}'
    response.headers['ETag'] = etag


@router.get('/branding', response_model=None)
def get_branding(request: Request, response: Response) -> dict[str, Any] | Response:
    """Return current instance branding configuration.

    Returns branding settings for the current instance including:
    - app_name: Application display name
    - app_description: Short description
    - bot_name: Chatbot persona name
    - logo_url: URL to logo image (may be null)
    - primary_color: Brand color in hex format

    Caching:
    - Cache-Control: public, max-age=3600 (1 hour)
    - ETag: Content-based hash for conditional requests
    - Supports If-None-Match for 304 Not Modified responses

    Args:
        request: Incoming HTTP request (for conditional headers).
        response: HTTP response (for setting cache headers).

    Returns:
        Branding configuration dict, or 304 Response if unchanged.
    """
    settings = get_settings()
    branding_data = settings.branding.model_dump()
    etag = _generate_etag(branding_data)

    # Handle conditional request (If-None-Match)
    if_none_match = request.headers.get('If-None-Match')
    if if_none_match == etag:
        return Response(
            status_code=304,
            headers={
                'ETag': etag,
                'Cache-Control': f'public, max-age={CACHE_MAX_AGE}'
            }
        )

    # Set caching headers for full response
    _set_cache_headers(response, etag)
    return branding_data
