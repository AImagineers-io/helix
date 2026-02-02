"""
Request Size Limits for protecting against oversized payloads.

Provides:
- Configurable size limits for different request types
- Path-based limit selection (chat vs upload vs general)
- ASGI middleware for enforcement
- 413 Payload Too Large responses with helpful messages

Limits:
- General requests: 1MB (default)
- File uploads: 10MB (for QA imports)
- Chat messages: 10KB (prevents abuse)
"""
import json
from dataclasses import dataclass
from typing import Callable, Awaitable

# Default limits
DEFAULT_MAX_REQUEST_SIZE = 1 * 1024 * 1024  # 1MB
DEFAULT_MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10MB
DEFAULT_MAX_CHAT_MESSAGE_SIZE = 10 * 1024  # 10KB

# Path patterns for different limit types
UPLOAD_PATH_PATTERNS = ["/qa/import", "/upload", "/files"]
CHAT_PATH_PATTERNS = ["/chat"]


class PayloadTooLargeError(Exception):
    """Raised when request payload exceeds size limit."""

    def __init__(self, max_size: int, actual_size: int, limit_type: str):
        self.max_size = max_size
        self.actual_size = actual_size
        self.limit_type = limit_type

        max_readable = self._format_bytes(max_size)
        actual_readable = self._format_bytes(actual_size)

        message = (
            f"Payload too large for {limit_type}: "
            f"{actual_readable} exceeds limit of {max_readable}"
        )
        super().__init__(message)

    @staticmethod
    def _format_bytes(size: int) -> str:
        """Format bytes as human-readable string."""
        if size >= 1024 * 1024:
            return f"{size / (1024 * 1024):.1f} MB"
        elif size >= 1024:
            return f"{size / 1024:.1f} KB"
        return f"{size} bytes"


@dataclass
class RequestLimits:
    """
    Configuration for request size limits.

    Attributes:
        max_request_size: General request size limit (bytes)
        max_upload_size: File upload size limit (bytes)
        max_chat_message_size: Chat message size limit (bytes)
    """
    max_request_size: int = DEFAULT_MAX_REQUEST_SIZE
    max_upload_size: int = DEFAULT_MAX_UPLOAD_SIZE
    max_chat_message_size: int = DEFAULT_MAX_CHAT_MESSAGE_SIZE

    def get_limit_for_type(self, limit_type: str) -> int:
        """Get the size limit for a given type."""
        if limit_type == "upload":
            return self.max_upload_size
        elif limit_type == "chat_message":
            return self.max_chat_message_size
        return self.max_request_size

    def get_limit_type_for_path(self, path: str) -> str:
        """
        Determine which limit type applies to a path.

        Args:
            path: Request path

        Returns:
            str: Limit type ("upload", "chat_message", or "request")
        """
        path_lower = path.lower()

        for pattern in UPLOAD_PATH_PATTERNS:
            if pattern in path_lower:
                return "upload"

        for pattern in CHAT_PATH_PATTERNS:
            if path_lower.startswith(pattern):
                return "chat_message"

        return "request"

    def check_content_length(self, content_length: int, limit_type: str) -> None:
        """
        Check if content length is within limits.

        Args:
            content_length: Size of request body in bytes
            limit_type: Type of limit to apply

        Raises:
            PayloadTooLargeError: If content exceeds limit
        """
        limit = self.get_limit_for_type(limit_type)

        if content_length > limit:
            raise PayloadTooLargeError(
                max_size=limit,
                actual_size=content_length,
                limit_type=limit_type
            )


class RequestSizeLimitMiddleware:
    """
    ASGI middleware that enforces request size limits.

    Checks Content-Length header and returns 413 if exceeded.
    Uses path-based rules to apply appropriate limits.
    """

    def __init__(
        self,
        app: Callable,
        limits: RequestLimits | None = None
    ):
        """
        Initialize middleware.

        Args:
            app: ASGI application
            limits: Request limits configuration
        """
        self.app = app
        self.limits = limits or RequestLimits()

    async def __call__(self, scope: dict, receive: Callable, send: Callable) -> None:
        """Handle ASGI request."""
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Extract headers
        headers = dict(scope.get("headers", []))
        content_length_header = headers.get(b"content-length")

        # Skip check for requests without body
        method = scope.get("method", "GET")
        if method in ("GET", "HEAD", "OPTIONS") and content_length_header is None:
            await self.app(scope, receive, send)
            return

        # Check content length if present
        if content_length_header is not None:
            try:
                content_length = int(content_length_header.decode())
                path = scope.get("path", "/")
                limit_type = self.limits.get_limit_type_for_path(path)

                self.limits.check_content_length(content_length, limit_type)

            except PayloadTooLargeError as e:
                await self._send_413_response(send, e)
                return
            except ValueError:
                # Invalid content-length header, let it through
                pass

        # Request is within limits, proceed
        await self.app(scope, receive, send)

    async def _send_413_response(
        self,
        send: Callable,
        error: PayloadTooLargeError
    ) -> None:
        """Send 413 Payload Too Large response."""
        body = json.dumps({
            "error": "Payload Too Large",
            "message": str(error),
            "max_size": error.max_size,
            "actual_size": error.actual_size,
            "limit_type": error.limit_type,
        }).encode()

        await send({
            "type": "http.response.start",
            "status": 413,
            "headers": [
                (b"content-type", b"application/json"),
                (b"content-length", str(len(body)).encode()),
            ],
        })

        await send({
            "type": "http.response.body",
            "body": body,
        })
