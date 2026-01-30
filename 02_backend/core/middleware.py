"""Middleware components for Helix.

This module contains middleware classes for request processing,
including authentication and security features.
"""
import base64
import binascii
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from core.config import get_settings, ENV_DEMO


class DemoAuthMiddleware(BaseHTTPMiddleware):
    """HTTP Basic Authentication middleware for demo environments.

    This middleware enforces basic authentication for demo environments
    while allowing certain paths (like /health and /branding) to be
    accessed without authentication.

    The middleware only activates when:
    - ENVIRONMENT is set to 'demo'
    - Demo credentials (DEMO_USERNAME, DEMO_PASSWORD) are configured

    Attributes:
        public_paths: List of paths that don't require authentication.
    """

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Response]
    ) -> Response:
        """Process the request through demo authentication.

        Args:
            request: The incoming HTTP request.
            call_next: The next middleware/handler in the chain.

        Returns:
            Response from the next handler or 401 if authentication fails.
        """
        settings = get_settings()

        # Only apply demo auth in demo environment
        if settings.environment != ENV_DEMO:
            return await call_next(request)

        # Skip if demo auth is not enabled (no credentials configured)
        if not settings.demo_auth.enabled:
            return await call_next(request)

        # Check if path is public
        path = request.url.path
        if self._is_public_path(path, settings.demo_auth.public_paths):
            return await call_next(request)

        # Validate basic auth
        if not self._validate_auth(request, settings):
            return Response(
                content='{"detail":"Authentication required"}',
                status_code=401,
                media_type="application/json",
                headers={"WWW-Authenticate": 'Basic realm="Demo Environment"'},
            )

        return await call_next(request)

    def _is_public_path(self, path: str, public_paths: list[str]) -> bool:
        """Check if a path is in the public paths list.

        Args:
            path: Request path to check.
            public_paths: List of paths that don't require auth.

        Returns:
            True if the path is public.
        """
        for public_path in public_paths:
            if path == public_path or path.startswith(public_path + '/'):
                return True
        return False

    def _validate_auth(self, request: Request, settings) -> bool:
        """Validate basic authentication credentials.

        Args:
            request: The incoming HTTP request.
            settings: Application settings.

        Returns:
            True if authentication is valid, False otherwise.
        """
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return False

        try:
            scheme, credentials = auth_header.split(" ", 1)
            if scheme.lower() != "basic":
                return False

            decoded = base64.b64decode(credentials).decode("utf-8")
            username, password = decoded.split(":", 1)

            return (
                username == settings.demo_auth.username and
                password == settings.demo_auth.password
            )
        except (ValueError, binascii.Error):
            return False
