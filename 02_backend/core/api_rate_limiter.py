"""
API Rate Limiter for per-API-key rate limiting.

Provides:
- Per API key request limits
- Per-minute and per-hour windows
- Retry-After calculation
- Abuse pattern detection
- Usage statistics

Default limits:
- 1000 requests/hour per admin key
- 60 requests/minute per device
"""
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional


# Default rate limits
DEFAULT_REQUESTS_PER_HOUR = 1000
DEFAULT_REQUESTS_PER_MINUTE = 60


@dataclass
class RateLimitConfig:
    """Configuration for rate limits."""
    requests_per_hour: int = DEFAULT_REQUESTS_PER_HOUR
    requests_per_minute: int = DEFAULT_REQUESTS_PER_MINUTE


@dataclass
class RateLimitResult:
    """Result of rate limit check."""
    allowed: bool
    remaining: int
    retry_after: Optional[int] = None
    limit: int = 0


def get_retry_after(window_seconds: int, elapsed: float) -> int:
    """
    Calculate seconds until rate limit window resets.

    Args:
        window_seconds: Size of the rate limit window
        elapsed: Seconds elapsed in current window

    Returns:
        int: Seconds until window resets
    """
    return max(1, int(window_seconds - elapsed))


class _TokenBucket:
    """Token bucket for rate limiting."""

    def __init__(self, capacity: int, window_seconds: int):
        self.capacity = capacity
        self.window_seconds = window_seconds
        self.tokens = capacity
        self.last_update = time.time()

    def consume(self) -> tuple[bool, int, Optional[int]]:
        """
        Try to consume a token.

        Returns:
            tuple: (allowed, remaining, retry_after)
        """
        now = time.time()
        elapsed = now - self.last_update

        # Refill tokens based on time elapsed
        if elapsed >= self.window_seconds:
            self.tokens = self.capacity
            self.last_update = now
            elapsed = 0

        if self.tokens > 0:
            self.tokens -= 1
            return True, self.tokens, None

        retry_after = get_retry_after(self.window_seconds, elapsed)
        return False, 0, retry_after

    def reset(self):
        """Reset the bucket."""
        self.tokens = self.capacity
        self.last_update = time.time()


class APIRateLimiter:
    """
    Rate limiter for API keys.

    Tracks requests per-minute and per-hour for each API key.
    Logs abuse patterns when keys are repeatedly blocked.
    """

    def __init__(self, config: Optional[RateLimitConfig] = None):
        """
        Initialize rate limiter.

        Args:
            config: Rate limit configuration
        """
        self.config = config or RateLimitConfig()
        self._minute_buckets: dict[str, _TokenBucket] = {}
        self._hour_buckets: dict[str, _TokenBucket] = {}
        self._abuse_counts: dict[str, int] = defaultdict(int)
        self._consecutive_blocks: dict[str, int] = defaultdict(int)

    def _get_minute_bucket(self, key: str) -> _TokenBucket:
        """Get or create minute bucket for key."""
        if key not in self._minute_buckets:
            self._minute_buckets[key] = _TokenBucket(
                self.config.requests_per_minute,
                60
            )
        return self._minute_buckets[key]

    def _get_hour_bucket(self, key: str) -> _TokenBucket:
        """Get or create hour bucket for key."""
        if key not in self._hour_buckets:
            self._hour_buckets[key] = _TokenBucket(
                self.config.requests_per_hour,
                3600
            )
        return self._hour_buckets[key]

    def check(self, key: str) -> RateLimitResult:
        """
        Check rate limit for API key.

        Args:
            key: API key or identifier

        Returns:
            RateLimitResult: Check result
        """
        minute_bucket = self._get_minute_bucket(key)
        hour_bucket = self._get_hour_bucket(key)

        # Check minute limit first (more restrictive)
        minute_allowed, minute_remaining, minute_retry = minute_bucket.consume()

        if not minute_allowed:
            self._record_block(key)
            return RateLimitResult(
                allowed=False,
                remaining=0,
                retry_after=minute_retry,
                limit=self.config.requests_per_minute
            )

        # Check hour limit
        hour_allowed, hour_remaining, hour_retry = hour_bucket.consume()

        if not hour_allowed:
            # Put the minute token back
            minute_bucket.tokens += 1
            self._record_block(key)
            return RateLimitResult(
                allowed=False,
                remaining=0,
                retry_after=hour_retry,
                limit=self.config.requests_per_hour
            )

        # Request allowed
        self._consecutive_blocks[key] = 0
        return RateLimitResult(
            allowed=True,
            remaining=min(minute_remaining, hour_remaining),
            limit=self.config.requests_per_minute
        )

    def _record_block(self, key: str):
        """Record a rate limit block for abuse detection."""
        self._consecutive_blocks[key] += 1

        # Log abuse after 3 consecutive blocks
        if self._consecutive_blocks[key] >= 3:
            self._abuse_counts[key] += 1

    def get_abuse_count(self, key: str) -> int:
        """
        Get abuse count for key.

        Args:
            key: API key

        Returns:
            int: Number of abuse incidents
        """
        return self._abuse_counts[key]

    def reset(self, key: str):
        """
        Reset limits for key.

        Args:
            key: API key to reset
        """
        if key in self._minute_buckets:
            self._minute_buckets[key].reset()
        if key in self._hour_buckets:
            self._hour_buckets[key].reset()
        self._consecutive_blocks[key] = 0

    def get_stats(self, key: str) -> dict:
        """
        Get usage statistics for key.

        Args:
            key: API key

        Returns:
            dict: Usage statistics
        """
        minute_bucket = self._get_minute_bucket(key)
        hour_bucket = self._get_hour_bucket(key)

        return {
            "requests_this_minute": self.config.requests_per_minute - minute_bucket.tokens,
            "requests_this_hour": self.config.requests_per_hour - hour_bucket.tokens,
            "minute_remaining": minute_bucket.tokens,
            "hour_remaining": hour_bucket.tokens,
            "abuse_count": self._abuse_counts[key],
        }


# Global limiter instance for convenience function
_global_limiter: Optional[APIRateLimiter] = None


def check_rate_limit(
    key: str,
    requests_per_minute: int = DEFAULT_REQUESTS_PER_MINUTE,
    requests_per_hour: int = DEFAULT_REQUESTS_PER_HOUR
) -> RateLimitResult:
    """
    Convenience function to check rate limit.

    Args:
        key: API key or identifier
        requests_per_minute: Minute limit
        requests_per_hour: Hour limit

    Returns:
        RateLimitResult: Check result
    """
    global _global_limiter

    if _global_limiter is None:
        _global_limiter = APIRateLimiter(
            RateLimitConfig(
                requests_per_minute=requests_per_minute,
                requests_per_hour=requests_per_hour
            )
        )

    return _global_limiter.check(key)
