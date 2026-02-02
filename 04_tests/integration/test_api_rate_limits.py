"""
Integration tests for API Rate Limiting per API Key (P12.4.3)

Tests rate limiting including:
- Per API key limits
- Per device limits (existing)
- 429 Too Many Requests response
- Retry-After header
- Abuse logging
"""
import pytest
import time

from core.api_rate_limiter import (
    RateLimitConfig,
    RateLimitResult,
    APIRateLimiter,
    check_rate_limit,
    get_retry_after,
)


class TestRateLimitConfig:
    """Tests for rate limit configuration."""

    def test_default_limits(self):
        """Default limits should be set."""
        config = RateLimitConfig()
        assert config.requests_per_hour > 0
        assert config.requests_per_minute > 0

    def test_custom_limits(self):
        """Custom limits should be accepted."""
        config = RateLimitConfig(
            requests_per_hour=500,
            requests_per_minute=30
        )
        assert config.requests_per_hour == 500
        assert config.requests_per_minute == 30


class TestRateLimitResult:
    """Tests for rate limit result."""

    def test_allowed_result(self):
        """Allowed result should have correct fields."""
        result = RateLimitResult(allowed=True, remaining=99)
        assert result.allowed is True
        assert result.remaining == 99
        assert result.retry_after is None

    def test_blocked_result(self):
        """Blocked result should include retry-after."""
        result = RateLimitResult(
            allowed=False,
            remaining=0,
            retry_after=60
        )
        assert result.allowed is False
        assert result.retry_after == 60


class TestRateLimitCheck:
    """Tests for rate limit checking."""

    def test_first_request_allowed(self):
        """First request should always be allowed."""
        limiter = APIRateLimiter()
        result = limiter.check("test-key-1")
        assert result.allowed is True

    def test_within_limits_allowed(self):
        """Requests within limits should be allowed."""
        config = RateLimitConfig(requests_per_minute=100)
        limiter = APIRateLimiter(config)

        for i in range(50):
            result = limiter.check(f"test-key-{i % 5}")
            assert result.allowed is True

    def test_over_limit_blocked(self):
        """Requests over limit should be blocked."""
        config = RateLimitConfig(requests_per_minute=5, requests_per_hour=100)
        limiter = APIRateLimiter(config)

        # Make requests up to limit
        for _ in range(5):
            limiter.check("over-limit-key")

        # Next request should be blocked
        result = limiter.check("over-limit-key")
        assert result.allowed is False

    def test_different_keys_tracked_separately(self):
        """Different API keys should have separate limits."""
        config = RateLimitConfig(requests_per_minute=3, requests_per_hour=100)
        limiter = APIRateLimiter(config)

        # Use up key1's limit
        for _ in range(3):
            limiter.check("key1")

        # key1 should be blocked
        result1 = limiter.check("key1")
        assert result1.allowed is False

        # key2 should still be allowed
        result2 = limiter.check("key2")
        assert result2.allowed is True


class TestRetryAfter:
    """Tests for retry-after calculation."""

    def test_retry_after_within_minute(self):
        """Retry-after should be seconds until window resets."""
        config = RateLimitConfig(requests_per_minute=2, requests_per_hour=1000)
        limiter = APIRateLimiter(config)

        # Use up limit
        limiter.check("retry-key")
        limiter.check("retry-key")

        # Get blocked result
        result = limiter.check("retry-key")
        assert result.retry_after is not None
        assert result.retry_after > 0
        assert result.retry_after <= 60

    def test_get_retry_after_function(self):
        """get_retry_after should return seconds."""
        seconds = get_retry_after(window_seconds=60, elapsed=30)
        assert seconds == 30


class TestRemainingCount:
    """Tests for remaining request count."""

    def test_remaining_decreases(self):
        """Remaining count should decrease with each request."""
        config = RateLimitConfig(requests_per_minute=10, requests_per_hour=1000)
        limiter = APIRateLimiter(config)

        result1 = limiter.check("remaining-key")
        result2 = limiter.check("remaining-key")

        assert result2.remaining < result1.remaining

    def test_remaining_is_zero_when_blocked(self):
        """Remaining should be zero when blocked."""
        config = RateLimitConfig(requests_per_minute=2, requests_per_hour=1000)
        limiter = APIRateLimiter(config)

        limiter.check("zero-key")
        limiter.check("zero-key")
        result = limiter.check("zero-key")

        assert result.remaining == 0


class TestAbuseLogging:
    """Tests for abuse pattern logging."""

    def test_logs_repeated_blocks(self):
        """Should log when key is repeatedly blocked."""
        config = RateLimitConfig(requests_per_minute=2, requests_per_hour=1000)
        limiter = APIRateLimiter(config)

        # Hit limit repeatedly
        for _ in range(10):
            limiter.check("abuse-key")

        # Should have abuse logged
        assert limiter.get_abuse_count("abuse-key") > 0

    def test_no_abuse_within_limits(self):
        """Should not log abuse for normal usage."""
        config = RateLimitConfig(requests_per_minute=100, requests_per_hour=1000)
        limiter = APIRateLimiter(config)

        for _ in range(10):
            limiter.check("normal-key")

        assert limiter.get_abuse_count("normal-key") == 0


class TestAPIRateLimiter:
    """Tests for the APIRateLimiter class."""

    @pytest.fixture
    def limiter(self):
        """Create rate limiter."""
        config = RateLimitConfig(
            requests_per_minute=10,
            requests_per_hour=100
        )
        return APIRateLimiter(config)

    def test_check_returns_result(self, limiter):
        """Check should return RateLimitResult."""
        result = limiter.check("test-api-key")
        assert isinstance(result, RateLimitResult)

    def test_reset_clears_counters(self, limiter):
        """Reset should clear all counters."""
        limiter.check("reset-key")
        limiter.check("reset-key")

        limiter.reset("reset-key")

        result = limiter.check("reset-key")
        # Should have full remaining again
        assert result.remaining >= limiter.config.requests_per_minute - 1

    def test_get_stats(self, limiter):
        """Should return usage stats."""
        for _ in range(5):
            limiter.check("stats-key")

        stats = limiter.get_stats("stats-key")
        assert stats["requests_this_minute"] == 5
        assert "requests_this_hour" in stats


class TestConvenienceFunction:
    """Tests for the check_rate_limit convenience function."""

    def test_check_rate_limit_basic(self):
        """Basic rate limit check should work."""
        result = check_rate_limit(
            key="func-test-key",
            requests_per_minute=100,
            requests_per_hour=1000
        )
        assert result.allowed is True

    def test_check_rate_limit_uses_defaults(self):
        """Should use default limits if not specified."""
        result = check_rate_limit(key="default-key")
        assert result.allowed is True
