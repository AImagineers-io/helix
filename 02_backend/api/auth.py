"""Authentication utilities for API endpoints."""
from fastapi import Header, HTTPException, Depends
from core.config import get_settings, Settings


def verify_api_key(
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
    settings: Settings = Depends(get_settings),
) -> str:
    """Verify API key from request header.

    Args:
        x_api_key: API key from X-API-Key header.
        settings: Application settings.

    Returns:
        The validated API key.

    Raises:
        HTTPException: If API key is missing, invalid, or not configured.
    """
    if not x_api_key:
        raise HTTPException(
            status_code=401,
            detail="API key required",
        )

    if not settings.api_key:
        raise HTTPException(
            status_code=500,
            detail="API key not configured on server",
        )

    if x_api_key != settings.api_key:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key",
        )

    return x_api_key
