"""
Integration tests for Request Size Limits (P12.2.2)

Tests request size limiting middleware:
- General request size limit (1MB)
- File upload limit (10MB)
- Chat message limit (10KB)
- 413 Payload Too Large responses
"""
import pytest
from unittest.mock import MagicMock, AsyncMock
from starlette.requests import Request
from starlette.responses import Response

from core.request_limits import (
    RequestLimits,
    RequestSizeLimitMiddleware,
    PayloadTooLargeError,
    DEFAULT_MAX_REQUEST_SIZE,
    DEFAULT_MAX_UPLOAD_SIZE,
    DEFAULT_MAX_CHAT_MESSAGE_SIZE,
)


class TestRequestLimitsConfig:
    """Tests for request limits configuration."""

    def test_default_max_request_size_1mb(self):
        """Default max request size should be 1MB."""
        assert DEFAULT_MAX_REQUEST_SIZE == 1 * 1024 * 1024  # 1MB

    def test_default_max_upload_size_10mb(self):
        """Default max upload size should be 10MB."""
        assert DEFAULT_MAX_UPLOAD_SIZE == 10 * 1024 * 1024  # 10MB

    def test_default_max_chat_message_10kb(self):
        """Default max chat message should be 10KB."""
        assert DEFAULT_MAX_CHAT_MESSAGE_SIZE == 10 * 1024  # 10KB

    def test_request_limits_accepts_custom_values(self):
        """RequestLimits should accept custom configuration."""
        limits = RequestLimits(
            max_request_size=2 * 1024 * 1024,
            max_upload_size=20 * 1024 * 1024,
            max_chat_message_size=5 * 1024
        )
        assert limits.max_request_size == 2 * 1024 * 1024
        assert limits.max_upload_size == 20 * 1024 * 1024
        assert limits.max_chat_message_size == 5 * 1024


class TestPayloadTooLargeError:
    """Tests for PayloadTooLargeError."""

    def test_error_contains_limit_info(self):
        """Error should contain limit information."""
        error = PayloadTooLargeError(
            max_size=1048576,
            actual_size=2097152,
            limit_type="request"
        )
        # Error message should contain human-readable sizes
        error_str = str(error).upper()
        assert "1.0 MB" in error_str or "1 MB" in error_str
        assert error.max_size == 1048576
        assert error.actual_size == 2097152

    def test_error_specifies_limit_type(self):
        """Error should specify which limit was exceeded."""
        error = PayloadTooLargeError(
            max_size=10240,
            actual_size=20480,
            limit_type="chat_message"
        )
        assert error.limit_type == "chat_message"


class TestRequestSizeValidation:
    """Tests for request size validation logic."""

    def test_check_content_length_under_limit_passes(self):
        """Request under limit should pass."""
        limits = RequestLimits()
        # Should not raise
        limits.check_content_length(500000, "request")  # 500KB

    def test_check_content_length_over_limit_raises(self):
        """Request over limit should raise error."""
        limits = RequestLimits()
        with pytest.raises(PayloadTooLargeError):
            limits.check_content_length(2 * 1024 * 1024, "request")  # 2MB

    def test_check_content_length_exact_limit_passes(self):
        """Request at exact limit should pass."""
        limits = RequestLimits()
        # Should not raise
        limits.check_content_length(DEFAULT_MAX_REQUEST_SIZE, "request")

    def test_upload_uses_upload_limit(self):
        """Upload requests should use the larger upload limit."""
        limits = RequestLimits()
        # 5MB should fail for general but pass for upload
        with pytest.raises(PayloadTooLargeError):
            limits.check_content_length(5 * 1024 * 1024, "request")

        # Should pass for upload
        limits.check_content_length(5 * 1024 * 1024, "upload")

    def test_chat_uses_message_limit(self):
        """Chat messages should use the smaller message limit."""
        limits = RequestLimits()
        # 50KB should pass for request but fail for chat
        limits.check_content_length(50 * 1024, "request")  # Passes

        with pytest.raises(PayloadTooLargeError):
            limits.check_content_length(50 * 1024, "chat_message")  # Fails


class TestPathBasedLimits:
    """Tests for path-based limit selection."""

    def test_chat_path_uses_message_limit(self):
        """Chat endpoint should use message limit."""
        limits = RequestLimits()
        limit_type = limits.get_limit_type_for_path("/chat")
        assert limit_type == "chat_message"

    def test_upload_path_uses_upload_limit(self):
        """Upload endpoints should use upload limit."""
        limits = RequestLimits()

        assert limits.get_limit_type_for_path("/qa/import/csv") == "upload"
        assert limits.get_limit_type_for_path("/qa/import/text") == "upload"
        assert limits.get_limit_type_for_path("/upload/file") == "upload"

    def test_general_path_uses_request_limit(self):
        """Other endpoints should use general request limit."""
        limits = RequestLimits()

        assert limits.get_limit_type_for_path("/health") == "request"
        assert limits.get_limit_type_for_path("/prompts") == "request"
        assert limits.get_limit_type_for_path("/api/users") == "request"


class TestMiddlewareIntegration:
    """Tests for middleware integration."""

    @pytest.fixture
    def limits(self):
        """Create request limits instance."""
        return RequestLimits()

    @pytest.fixture
    def mock_app(self):
        """Create mock ASGI app."""
        async def app(scope, receive, send):
            response = Response(content="OK", status_code=200)
            await response(scope, receive, send)
        return app

    @pytest.mark.asyncio
    async def test_middleware_allows_valid_request(self, limits, mock_app):
        """Middleware should allow requests under limit."""
        middleware = RequestSizeLimitMiddleware(mock_app, limits)

        # Create mock scope with small content length
        scope = {
            "type": "http",
            "method": "POST",
            "path": "/api/data",
            "headers": [(b"content-length", b"1000")],
        }

        response_started = False
        response_status = None

        async def receive():
            return {"type": "http.request", "body": b"x" * 1000}

        async def send(message):
            nonlocal response_started, response_status
            if message["type"] == "http.response.start":
                response_started = True
                response_status = message["status"]

        await middleware(scope, receive, send)

        assert response_started
        assert response_status == 200

    @pytest.mark.asyncio
    async def test_middleware_rejects_large_request(self, limits, mock_app):
        """Middleware should reject requests over limit."""
        middleware = RequestSizeLimitMiddleware(mock_app, limits)

        # Create mock scope with large content length
        large_size = 2 * 1024 * 1024  # 2MB
        scope = {
            "type": "http",
            "method": "POST",
            "path": "/api/data",
            "headers": [(b"content-length", str(large_size).encode())],
        }

        response_status = None

        async def receive():
            return {"type": "http.request", "body": b"x" * large_size}

        async def send(message):
            nonlocal response_status
            if message["type"] == "http.response.start":
                response_status = message["status"]

        await middleware(scope, receive, send)

        assert response_status == 413

    @pytest.mark.asyncio
    async def test_middleware_returns_helpful_message(self, limits, mock_app):
        """413 response should include helpful error message."""
        middleware = RequestSizeLimitMiddleware(mock_app, limits)

        large_size = 2 * 1024 * 1024
        scope = {
            "type": "http",
            "method": "POST",
            "path": "/api/data",
            "headers": [(b"content-length", str(large_size).encode())],
        }

        response_body = b""

        async def receive():
            return {"type": "http.request", "body": b"x" * large_size}

        async def send(message):
            nonlocal response_body
            if message["type"] == "http.response.body":
                response_body = message.get("body", b"")

        await middleware(scope, receive, send)

        # Response should contain error message
        assert b"Payload Too Large" in response_body or b"too large" in response_body.lower()


class TestContentLengthMissing:
    """Tests for handling missing Content-Length header."""

    @pytest.fixture
    def limits(self):
        return RequestLimits()

    @pytest.fixture
    def mock_app(self):
        async def app(scope, receive, send):
            response = Response(content="OK", status_code=200)
            await response(scope, receive, send)
        return app

    @pytest.mark.asyncio
    async def test_missing_content_length_allowed_for_get(self, limits, mock_app):
        """GET requests without Content-Length should be allowed."""
        middleware = RequestSizeLimitMiddleware(mock_app, limits)

        scope = {
            "type": "http",
            "method": "GET",
            "path": "/api/data",
            "headers": [],
        }

        response_status = None

        async def receive():
            return {"type": "http.request", "body": b""}

        async def send(message):
            nonlocal response_status
            if message["type"] == "http.response.start":
                response_status = message["status"]

        await middleware(scope, receive, send)

        assert response_status == 200
