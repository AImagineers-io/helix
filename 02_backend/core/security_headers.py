"""
Security Headers Configuration and Middleware.

Provides:
- Content Security Policy (CSP)
- X-Frame-Options
- X-Content-Type-Options
- X-XSS-Protection
- HSTS (HTTP Strict Transport Security)
- Referrer-Policy
- Permissions-Policy
- Nonce generation for inline scripts
"""
import base64
import secrets
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class SecurityHeadersConfig:
    """Configuration for security headers."""
    # X-Frame-Options: DENY, SAMEORIGIN, or ALLOW-FROM
    frame_options: str = "DENY"

    # X-Content-Type-Options
    content_type_options: str = "nosniff"

    # X-XSS-Protection
    xss_protection: str = "1; mode=block"

    # HSTS
    enable_hsts: bool = False
    hsts_max_age: int = 31536000  # 1 year
    hsts_include_subdomains: bool = True
    hsts_preload: bool = False

    # Referrer Policy
    referrer_policy: str = "strict-origin-when-cross-origin"

    # CSP directives
    csp_default_src: list[str] = field(default_factory=lambda: ["'self'"])
    csp_script_src: list[str] = field(default_factory=lambda: ["'self'"])
    csp_style_src: list[str] = field(default_factory=lambda: ["'self'", "'unsafe-inline'"])
    csp_img_src: list[str] = field(default_factory=lambda: ["'self'", "data:", "https:"])
    csp_connect_src: list[str] = field(default_factory=lambda: ["'self'"])
    csp_font_src: list[str] = field(default_factory=lambda: ["'self'"])
    csp_frame_ancestors: list[str] = field(default_factory=lambda: ["'none'"])

    # Additional sources
    additional_script_sources: list[str] = field(default_factory=list)
    additional_style_sources: list[str] = field(default_factory=list)

    # Permissions Policy
    permissions_policy: dict[str, list[str]] = field(default_factory=lambda: {
        "geolocation": [],
        "microphone": [],
        "camera": [],
        "payment": [],
    })


def generate_nonce() -> str:
    """
    Generate a cryptographic nonce for CSP.

    Returns:
        str: Base64-encoded random nonce
    """
    return base64.b64encode(secrets.token_bytes(16)).decode("utf-8")


def generate_csp_header(
    config: SecurityHeadersConfig,
    nonce: Optional[str] = None
) -> str:
    """
    Generate Content-Security-Policy header value.

    Args:
        config: Security headers configuration
        nonce: Optional nonce for inline scripts

    Returns:
        str: CSP header value
    """
    directives = []

    # default-src
    directives.append(f"default-src {' '.join(config.csp_default_src)}")

    # script-src with optional nonce
    script_sources = config.csp_script_src.copy()
    if config.additional_script_sources:
        script_sources.extend(config.additional_script_sources)
    if nonce:
        script_sources.append(f"'nonce-{nonce}'")
    directives.append(f"script-src {' '.join(script_sources)}")

    # style-src
    style_sources = config.csp_style_src.copy()
    if config.additional_style_sources:
        style_sources.extend(config.additional_style_sources)
    directives.append(f"style-src {' '.join(style_sources)}")

    # img-src
    directives.append(f"img-src {' '.join(config.csp_img_src)}")

    # connect-src
    directives.append(f"connect-src {' '.join(config.csp_connect_src)}")

    # font-src
    directives.append(f"font-src {' '.join(config.csp_font_src)}")

    # frame-ancestors
    directives.append(f"frame-ancestors {' '.join(config.csp_frame_ancestors)}")

    return "; ".join(directives)


def _generate_permissions_policy(config: SecurityHeadersConfig) -> str:
    """
    Generate Permissions-Policy header value.

    Args:
        config: Security headers configuration

    Returns:
        str: Permissions-Policy header value
    """
    policies = []
    for feature, allowlist in config.permissions_policy.items():
        if not allowlist:
            policies.append(f"{feature}=()")
        else:
            allowed = " ".join(f'"{a}"' for a in allowlist)
            policies.append(f"{feature}=({allowed})")
    return ", ".join(policies)


def get_security_headers(
    config: SecurityHeadersConfig,
    nonce: Optional[str] = None
) -> dict[str, str]:
    """
    Generate all security headers.

    Args:
        config: Security headers configuration
        nonce: Optional nonce for CSP

    Returns:
        dict: Security headers
    """
    headers = {}

    # Content-Security-Policy
    headers["Content-Security-Policy"] = generate_csp_header(config, nonce)

    # X-Frame-Options
    headers["X-Frame-Options"] = config.frame_options

    # X-Content-Type-Options
    headers["X-Content-Type-Options"] = config.content_type_options

    # X-XSS-Protection
    headers["X-XSS-Protection"] = config.xss_protection

    # HSTS
    if config.enable_hsts:
        hsts_value = f"max-age={config.hsts_max_age}"
        if config.hsts_include_subdomains:
            hsts_value += "; includeSubDomains"
        if config.hsts_preload:
            hsts_value += "; preload"
        headers["Strict-Transport-Security"] = hsts_value

    # Referrer-Policy
    headers["Referrer-Policy"] = config.referrer_policy

    # Permissions-Policy
    headers["Permissions-Policy"] = _generate_permissions_policy(config)

    return headers


class SecurityHeadersMiddleware:
    """
    ASGI middleware for adding security headers.

    Adds CSP, X-Frame-Options, and other security headers to all responses.
    """

    def __init__(self, app, config: SecurityHeadersConfig):
        """
        Initialize security headers middleware.

        Args:
            app: ASGI application
            config: Security headers configuration
        """
        self.app = app
        self.config = config

    async def __call__(self, scope, receive, send):
        """Handle ASGI request."""
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Generate nonce for this request
        nonce = generate_nonce()
        scope["csp_nonce"] = nonce

        # Wrap send to add security headers
        async def send_with_headers(message):
            if message["type"] == "http.response.start":
                security_headers = get_security_headers(self.config, nonce)

                existing_headers = list(message.get("headers", []))

                for name, value in security_headers.items():
                    existing_headers.append(
                        (name.lower().encode(), value.encode())
                    )

                message = {
                    **message,
                    "headers": existing_headers,
                }

            await send(message)

        await self.app(scope, receive, send_with_headers)
