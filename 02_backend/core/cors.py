"""
CORS Configuration and Middleware.

Provides:
- Configurable allowed origins
- Allowed methods and headers
- Preflight request handling
- Credentials support

Default: Strict same-origin for admin, configurable for widget.
"""
from dataclasses import dataclass, field
from typing import Optional


# Default allowed methods
DEFAULT_ALLOWED_METHODS = ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"]

# Default allowed headers
DEFAULT_ALLOWED_HEADERS = [
    "Accept",
    "Accept-Language",
    "Content-Language",
    "Content-Type",
    "Authorization",
    "X-Requested-With",
    "X-Request-ID",
]

# Default max age for preflight caching (1 hour)
DEFAULT_MAX_AGE = 3600


@dataclass
class CORSConfig:
    """Configuration for CORS."""
    allowed_origins: list[str] = field(default_factory=list)
    allowed_methods: list[str] = field(default_factory=lambda: DEFAULT_ALLOWED_METHODS.copy())
    allowed_headers: list[str] = field(default_factory=lambda: DEFAULT_ALLOWED_HEADERS.copy())
    expose_headers: list[str] = field(default_factory=list)
    allow_credentials: bool = True
    max_age: int = DEFAULT_MAX_AGE


def is_origin_allowed(origin: Optional[str], config: CORSConfig) -> bool:
    """
    Check if origin is allowed by CORS config.

    Args:
        origin: Request origin header value
        config: CORS configuration

    Returns:
        bool: True if origin is allowed
    """
    if not origin:
        return False

    # Wildcard allows all
    if "*" in config.allowed_origins:
        return True

    # Exact match required
    return origin in config.allowed_origins


def get_cors_headers(
    origin: str,
    config: CORSConfig,
    preflight: bool = False
) -> dict[str, str]:
    """
    Generate CORS headers for a response.

    Args:
        origin: Request origin
        config: CORS configuration
        preflight: Whether this is a preflight response

    Returns:
        dict: CORS headers to add to response
    """
    if not is_origin_allowed(origin, config):
        return {}

    headers = {}

    # Allow-Origin: echo back the origin (not wildcard when credentials)
    if config.allow_credentials:
        headers["Access-Control-Allow-Origin"] = origin
    elif "*" in config.allowed_origins:
        headers["Access-Control-Allow-Origin"] = "*"
    else:
        headers["Access-Control-Allow-Origin"] = origin

    # Allow-Methods
    headers["Access-Control-Allow-Methods"] = ", ".join(config.allowed_methods)

    # Allow-Headers
    headers["Access-Control-Allow-Headers"] = ", ".join(config.allowed_headers)

    # Allow-Credentials
    if config.allow_credentials:
        headers["Access-Control-Allow-Credentials"] = "true"

    # Preflight-specific headers
    if preflight:
        headers["Access-Control-Max-Age"] = str(config.max_age)

        if config.expose_headers:
            headers["Access-Control-Expose-Headers"] = ", ".join(config.expose_headers)

    return headers


class CORSMiddleware:
    """
    ASGI middleware for CORS handling.

    Adds CORS headers to responses and handles preflight requests.
    """

    def __init__(self, app, config: CORSConfig):
        """
        Initialize CORS middleware.

        Args:
            app: ASGI application
            config: CORS configuration
        """
        self.app = app
        self.config = config

    async def __call__(self, scope, receive, send):
        """Handle ASGI request."""
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Extract origin from headers
        origin = None
        for header_name, header_value in scope.get("headers", []):
            if header_name == b"origin":
                origin = header_value.decode("utf-8")
                break

        # Handle preflight OPTIONS request
        if scope["method"] == "OPTIONS" and origin:
            is_preflight = False
            for header_name, _ in scope.get("headers", []):
                if header_name == b"access-control-request-method":
                    is_preflight = True
                    break

            if is_preflight:
                await self._send_preflight_response(send, origin)
                return

        # Wrap send to add CORS headers
        async def send_with_cors(message):
            if message["type"] == "http.response.start" and origin:
                cors_headers = get_cors_headers(origin, self.config)

                # Convert existing headers to dict
                existing_headers = list(message.get("headers", []))

                # Add CORS headers
                for name, value in cors_headers.items():
                    existing_headers.append(
                        (name.lower().encode(), value.encode())
                    )

                message = {
                    **message,
                    "headers": existing_headers,
                }

            await send(message)

        await self.app(scope, receive, send_with_cors)

    async def _send_preflight_response(self, send, origin: str):
        """Send preflight response."""
        cors_headers = get_cors_headers(origin, self.config, preflight=True)

        headers = [
            (name.lower().encode(), value.encode())
            for name, value in cors_headers.items()
        ]

        await send({
            "type": "http.response.start",
            "status": 204,
            "headers": headers,
        })
        await send({
            "type": "http.response.body",
            "body": b"",
        })
