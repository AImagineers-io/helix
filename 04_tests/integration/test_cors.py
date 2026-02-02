"""
Integration tests for CORS Configuration (P12.4.1)

Tests CORS including:
- Allowed origins whitelist
- Allowed methods configuration
- Allowed headers configuration
- Preflight requests
- Credentials handling
"""
import pytest

from core.cors import (
    CORSConfig,
    CORSMiddleware,
    is_origin_allowed,
    get_cors_headers,
)


class TestCORSConfig:
    """Tests for CORS configuration."""

    def test_default_config(self):
        """Default config should be restrictive."""
        config = CORSConfig()
        assert config.allow_credentials is True
        assert "GET" in config.allowed_methods
        assert "POST" in config.allowed_methods

    def test_custom_origins(self):
        """Custom origins should be accepted."""
        config = CORSConfig(
            allowed_origins=["https://example.com", "https://app.example.com"]
        )
        assert "https://example.com" in config.allowed_origins
        assert "https://app.example.com" in config.allowed_origins

    def test_wildcard_origin(self):
        """Wildcard origin should be configurable."""
        config = CORSConfig(allowed_origins=["*"])
        assert "*" in config.allowed_origins


class TestOriginValidation:
    """Tests for origin validation."""

    def test_exact_match_allowed(self):
        """Exact origin match should be allowed."""
        config = CORSConfig(allowed_origins=["https://example.com"])
        assert is_origin_allowed("https://example.com", config) is True

    def test_different_origin_blocked(self):
        """Different origin should be blocked."""
        config = CORSConfig(allowed_origins=["https://example.com"])
        assert is_origin_allowed("https://evil.com", config) is False

    def test_wildcard_allows_all(self):
        """Wildcard should allow any origin."""
        config = CORSConfig(allowed_origins=["*"])
        assert is_origin_allowed("https://anything.com", config) is True

    def test_subdomain_not_matched_by_parent(self):
        """Subdomain should not match parent domain."""
        config = CORSConfig(allowed_origins=["https://example.com"])
        assert is_origin_allowed("https://sub.example.com", config) is False

    def test_http_not_matched_by_https(self):
        """HTTP should not match HTTPS origin."""
        config = CORSConfig(allowed_origins=["https://example.com"])
        assert is_origin_allowed("http://example.com", config) is False

    def test_port_must_match(self):
        """Port must match exactly."""
        config = CORSConfig(allowed_origins=["https://example.com:8080"])
        assert is_origin_allowed("https://example.com:8080", config) is True
        assert is_origin_allowed("https://example.com:9090", config) is False

    def test_empty_origin_blocked(self):
        """Empty origin should be blocked."""
        config = CORSConfig(allowed_origins=["https://example.com"])
        assert is_origin_allowed("", config) is False
        assert is_origin_allowed(None, config) is False


class TestCORSHeaders:
    """Tests for CORS header generation."""

    def test_generates_allow_origin(self):
        """Should generate Access-Control-Allow-Origin."""
        config = CORSConfig(allowed_origins=["https://example.com"])
        headers = get_cors_headers("https://example.com", config)
        assert headers["Access-Control-Allow-Origin"] == "https://example.com"

    def test_generates_allow_methods(self):
        """Should generate Access-Control-Allow-Methods."""
        config = CORSConfig(
            allowed_origins=["*"],
            allowed_methods=["GET", "POST", "PUT"]
        )
        headers = get_cors_headers("https://example.com", config)
        assert "GET" in headers["Access-Control-Allow-Methods"]
        assert "POST" in headers["Access-Control-Allow-Methods"]
        assert "PUT" in headers["Access-Control-Allow-Methods"]

    def test_generates_allow_headers(self):
        """Should generate Access-Control-Allow-Headers."""
        config = CORSConfig(
            allowed_origins=["*"],
            allowed_headers=["Content-Type", "Authorization"]
        )
        headers = get_cors_headers("https://example.com", config)
        assert "Content-Type" in headers["Access-Control-Allow-Headers"]
        assert "Authorization" in headers["Access-Control-Allow-Headers"]

    def test_generates_credentials_header(self):
        """Should generate Access-Control-Allow-Credentials."""
        config = CORSConfig(allowed_origins=["*"], allow_credentials=True)
        headers = get_cors_headers("https://example.com", config)
        assert headers["Access-Control-Allow-Credentials"] == "true"

    def test_generates_max_age(self):
        """Should generate Access-Control-Max-Age for preflight caching."""
        config = CORSConfig(allowed_origins=["*"], max_age=3600)
        headers = get_cors_headers("https://example.com", config, preflight=True)
        assert headers["Access-Control-Max-Age"] == "3600"

    def test_no_headers_for_blocked_origin(self):
        """Should return empty headers for blocked origin."""
        config = CORSConfig(allowed_origins=["https://example.com"])
        headers = get_cors_headers("https://evil.com", config)
        assert headers == {}


class TestPreflightRequests:
    """Tests for preflight request handling."""

    def test_preflight_includes_max_age(self):
        """Preflight response should include max-age."""
        config = CORSConfig(allowed_origins=["*"], max_age=7200)
        headers = get_cors_headers("https://example.com", config, preflight=True)
        assert "Access-Control-Max-Age" in headers
        assert headers["Access-Control-Max-Age"] == "7200"

    def test_preflight_includes_expose_headers(self):
        """Preflight response should include expose headers."""
        config = CORSConfig(
            allowed_origins=["*"],
            expose_headers=["X-Custom-Header", "X-Request-Id"]
        )
        headers = get_cors_headers("https://example.com", config, preflight=True)
        assert "Access-Control-Expose-Headers" in headers


class TestCORSMiddleware:
    """Tests for CORS middleware."""

    @pytest.fixture
    def config(self):
        """Create test CORS config."""
        return CORSConfig(
            allowed_origins=["https://example.com", "https://admin.example.com"],
            allowed_methods=["GET", "POST", "PUT", "DELETE"],
            allowed_headers=["Content-Type", "Authorization"],
            allow_credentials=True,
            max_age=3600
        )

    @pytest.fixture
    def middleware(self, config):
        """Create CORS middleware."""
        async def app(scope, receive, send):
            await send({
                "type": "http.response.start",
                "status": 200,
                "headers": [[b"content-type", b"application/json"]],
            })
            await send({
                "type": "http.response.body",
                "body": b'{"status": "ok"}',
            })
        return CORSMiddleware(app, config)

    @pytest.mark.asyncio
    async def test_adds_cors_headers_to_response(self, middleware):
        """Middleware should add CORS headers to allowed origins."""
        scope = {
            "type": "http",
            "method": "GET",
            "headers": [(b"origin", b"https://example.com")],
        }

        responses = []
        async def receive():
            return {"type": "http.request", "body": b""}

        async def send(message):
            responses.append(message)

        await middleware(scope, receive, send)

        # Find response start
        start = next(r for r in responses if r["type"] == "http.response.start")
        headers_dict = {k.decode(): v.decode() for k, v in start["headers"]}

        assert "access-control-allow-origin" in headers_dict

    @pytest.mark.asyncio
    async def test_handles_preflight_request(self, middleware):
        """Middleware should handle OPTIONS preflight requests."""
        scope = {
            "type": "http",
            "method": "OPTIONS",
            "headers": [
                (b"origin", b"https://example.com"),
                (b"access-control-request-method", b"POST"),
            ],
        }

        responses = []
        async def receive():
            return {"type": "http.request", "body": b""}

        async def send(message):
            responses.append(message)

        await middleware(scope, receive, send)

        start = next(r for r in responses if r["type"] == "http.response.start")
        # Preflight should return 204 No Content
        assert start["status"] == 204

    @pytest.mark.asyncio
    async def test_blocks_disallowed_origin(self, middleware):
        """Middleware should not add CORS headers for disallowed origins."""
        scope = {
            "type": "http",
            "method": "GET",
            "headers": [(b"origin", b"https://evil.com")],
        }

        responses = []
        async def receive():
            return {"type": "http.request", "body": b""}

        async def send(message):
            responses.append(message)

        await middleware(scope, receive, send)

        start = next(r for r in responses if r["type"] == "http.response.start")
        headers_dict = {k.decode(): v.decode() for k, v in start["headers"]}

        assert "access-control-allow-origin" not in headers_dict

    @pytest.mark.asyncio
    async def test_passes_through_non_cors_requests(self, middleware):
        """Middleware should pass through requests without Origin header."""
        scope = {
            "type": "http",
            "method": "GET",
            "headers": [],  # No Origin header
        }

        responses = []
        async def receive():
            return {"type": "http.request", "body": b""}

        async def send(message):
            responses.append(message)

        await middleware(scope, receive, send)

        # Should still get response
        assert any(r["type"] == "http.response.body" for r in responses)
