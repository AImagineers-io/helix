"""
Integration tests for Content Security Policy (P12.4.2)

Tests CSP headers including:
- CSP header generation
- X-Frame-Options
- X-Content-Type-Options
- X-XSS-Protection
- Nonce generation for inline scripts
"""
import pytest

from core.security_headers import (
    SecurityHeadersConfig,
    SecurityHeadersMiddleware,
    generate_csp_header,
    generate_nonce,
    get_security_headers,
)


class TestSecurityHeadersConfig:
    """Tests for security headers configuration."""

    def test_default_config(self):
        """Default config should have secure defaults."""
        config = SecurityHeadersConfig()
        assert config.frame_options == "DENY"
        assert config.content_type_options == "nosniff"
        assert config.xss_protection == "1; mode=block"

    def test_custom_frame_options(self):
        """Custom frame options should be accepted."""
        config = SecurityHeadersConfig(frame_options="SAMEORIGIN")
        assert config.frame_options == "SAMEORIGIN"


class TestNonceGeneration:
    """Tests for nonce generation."""

    def test_generates_nonce(self):
        """Should generate a nonce string."""
        nonce = generate_nonce()
        assert nonce is not None
        assert len(nonce) > 0

    def test_nonces_are_unique(self):
        """Each nonce should be unique."""
        nonces = [generate_nonce() for _ in range(100)]
        assert len(set(nonces)) == 100

    def test_nonce_is_base64(self):
        """Nonce should be base64 encoded."""
        nonce = generate_nonce()
        # Base64 characters only
        import re
        assert re.match(r'^[A-Za-z0-9+/=]+$', nonce)


class TestCSPHeaderGeneration:
    """Tests for CSP header generation."""

    def test_default_csp(self):
        """Default CSP should be restrictive."""
        config = SecurityHeadersConfig()
        csp = generate_csp_header(config)
        assert "default-src" in csp
        assert "'self'" in csp

    def test_script_src_with_nonce(self):
        """CSP should include nonce for scripts."""
        config = SecurityHeadersConfig()
        nonce = generate_nonce()
        csp = generate_csp_header(config, nonce=nonce)
        assert f"'nonce-{nonce}'" in csp

    def test_style_src_directive(self):
        """CSP should include style-src directive."""
        config = SecurityHeadersConfig()
        csp = generate_csp_header(config)
        assert "style-src" in csp

    def test_img_src_directive(self):
        """CSP should include img-src directive."""
        config = SecurityHeadersConfig()
        csp = generate_csp_header(config)
        assert "img-src" in csp

    def test_connect_src_directive(self):
        """CSP should include connect-src directive."""
        config = SecurityHeadersConfig()
        csp = generate_csp_header(config)
        assert "connect-src" in csp

    def test_frame_ancestors_directive(self):
        """CSP should include frame-ancestors directive."""
        config = SecurityHeadersConfig()
        csp = generate_csp_header(config)
        assert "frame-ancestors" in csp

    def test_custom_script_sources(self):
        """Custom script sources should be included."""
        config = SecurityHeadersConfig(
            additional_script_sources=["https://cdn.example.com"]
        )
        csp = generate_csp_header(config)
        assert "https://cdn.example.com" in csp

    def test_custom_style_sources(self):
        """Custom style sources should be included."""
        config = SecurityHeadersConfig(
            additional_style_sources=["https://fonts.googleapis.com"]
        )
        csp = generate_csp_header(config)
        assert "https://fonts.googleapis.com" in csp


class TestSecurityHeaders:
    """Tests for security header generation."""

    def test_includes_csp(self):
        """Should include Content-Security-Policy header."""
        config = SecurityHeadersConfig()
        headers = get_security_headers(config)
        assert "Content-Security-Policy" in headers

    def test_includes_x_frame_options(self):
        """Should include X-Frame-Options header."""
        config = SecurityHeadersConfig()
        headers = get_security_headers(config)
        assert headers["X-Frame-Options"] == "DENY"

    def test_includes_x_content_type_options(self):
        """Should include X-Content-Type-Options header."""
        config = SecurityHeadersConfig()
        headers = get_security_headers(config)
        assert headers["X-Content-Type-Options"] == "nosniff"

    def test_includes_x_xss_protection(self):
        """Should include X-XSS-Protection header."""
        config = SecurityHeadersConfig()
        headers = get_security_headers(config)
        assert headers["X-XSS-Protection"] == "1; mode=block"

    def test_includes_strict_transport_security(self):
        """Should include Strict-Transport-Security header."""
        config = SecurityHeadersConfig(enable_hsts=True)
        headers = get_security_headers(config)
        assert "Strict-Transport-Security" in headers
        assert "max-age" in headers["Strict-Transport-Security"]

    def test_referrer_policy(self):
        """Should include Referrer-Policy header."""
        config = SecurityHeadersConfig()
        headers = get_security_headers(config)
        assert "Referrer-Policy" in headers

    def test_permissions_policy(self):
        """Should include Permissions-Policy header."""
        config = SecurityHeadersConfig()
        headers = get_security_headers(config)
        assert "Permissions-Policy" in headers


class TestSecurityHeadersMiddleware:
    """Tests for security headers middleware."""

    @pytest.fixture
    def config(self):
        """Create test config."""
        return SecurityHeadersConfig(enable_hsts=True)

    @pytest.fixture
    def middleware(self, config):
        """Create middleware."""
        async def app(scope, receive, send):
            await send({
                "type": "http.response.start",
                "status": 200,
                "headers": [[b"content-type", b"text/html"]],
            })
            await send({
                "type": "http.response.body",
                "body": b"<html><body>Test</body></html>",
            })
        return SecurityHeadersMiddleware(app, config)

    @pytest.mark.asyncio
    async def test_adds_security_headers(self, middleware):
        """Middleware should add security headers."""
        scope = {"type": "http", "method": "GET", "headers": []}

        responses = []
        async def receive():
            return {"type": "http.request", "body": b""}

        async def send(message):
            responses.append(message)

        await middleware(scope, receive, send)

        start = next(r for r in responses if r["type"] == "http.response.start")
        headers_dict = {k.decode(): v.decode() for k, v in start["headers"]}

        assert "content-security-policy" in headers_dict
        assert "x-frame-options" in headers_dict
        assert "x-content-type-options" in headers_dict

    @pytest.mark.asyncio
    async def test_sets_nonce_in_scope(self, middleware):
        """Middleware should set nonce in scope for templates."""
        nonce_value = None

        async def test_app(scope, receive, send):
            nonlocal nonce_value
            nonce_value = scope.get("csp_nonce")
            await send({
                "type": "http.response.start",
                "status": 200,
                "headers": [],
            })
            await send({
                "type": "http.response.body",
                "body": b"",
            })

        config = SecurityHeadersConfig()
        middleware = SecurityHeadersMiddleware(test_app, config)

        scope = {"type": "http", "method": "GET", "headers": []}
        async def receive():
            return {"type": "http.request", "body": b""}
        async def send(message):
            pass

        await middleware(scope, receive, send)

        assert nonce_value is not None

    @pytest.mark.asyncio
    async def test_skips_non_http(self, middleware):
        """Middleware should skip non-HTTP requests."""
        scope = {"type": "websocket"}

        called = False
        async def test_app(scope, receive, send):
            nonlocal called
            called = True

        config = SecurityHeadersConfig()
        middleware = SecurityHeadersMiddleware(test_app, config)

        await middleware(scope, None, None)
        assert called
