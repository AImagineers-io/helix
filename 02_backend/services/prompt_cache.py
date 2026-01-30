"""
Prompt caching service using Redis.

Provides caching layer for active prompts with automatic invalidation.
"""
import logging
from typing import Optional, Callable, Any

logger = logging.getLogger(__name__)


class PromptCacheService:
    """Service for caching active prompts in Redis.

    Implements read-through caching with TTL-based expiration and
    explicit invalidation on publish.

    Attributes:
        CACHE_TTL: Time-to-live for cached prompts (1 hour).
        KEY_PREFIX: Prefix for all prompt cache keys.
    """

    CACHE_TTL = 3600  # 1 hour in seconds
    KEY_PREFIX = "prompt:"

    def __init__(self, redis_client: Any):
        """Initialize cache service with Redis client.

        Args:
            redis_client: Redis client instance (or mock for testing).
        """
        self._redis = redis_client

    @classmethod
    def get_cache_key(cls, prompt_type: str) -> str:
        """Generate cache key for a prompt type.

        Args:
            prompt_type: The type of prompt (e.g., 'system_prompt').

        Returns:
            Cache key string.
        """
        return f"{cls.KEY_PREFIX}{prompt_type}"

    def get_cached_prompt(self, prompt_type: str) -> Optional[str]:
        """Get cached prompt content by type.

        Args:
            prompt_type: The type of prompt to retrieve.

        Returns:
            Cached content if found, None otherwise.
        """
        try:
            key = self.get_cache_key(prompt_type)
            result = self._redis.get(key)
            if result is not None:
                logger.debug(f"Cache hit for prompt type: {prompt_type}")
                return result.decode('utf-8') if isinstance(result, bytes) else result
            logger.debug(f"Cache miss for prompt type: {prompt_type}")
            return None
        except Exception as e:
            logger.warning(f"Redis get failed for {prompt_type}: {e}")
            return None

    def set_cached_prompt(self, prompt_type: str, content: str) -> bool:
        """Cache prompt content with TTL.

        Args:
            prompt_type: The type of prompt.
            content: The prompt content to cache.

        Returns:
            True if cached successfully, False otherwise.
        """
        try:
            key = self.get_cache_key(prompt_type)
            self._redis.setex(key, self.CACHE_TTL, content)
            logger.debug(f"Cached prompt type: {prompt_type} (TTL: {self.CACHE_TTL}s)")
            return True
        except Exception as e:
            logger.warning(f"Redis set failed for {prompt_type}: {e}")
            return False

    def invalidate_prompt(self, prompt_type: str) -> bool:
        """Invalidate cached prompt for a type.

        Args:
            prompt_type: The type of prompt to invalidate.

        Returns:
            True if invalidated successfully, False otherwise.
        """
        try:
            key = self.get_cache_key(prompt_type)
            self._redis.delete(key)
            logger.info(f"Invalidated cache for prompt type: {prompt_type}")
            return True
        except Exception as e:
            logger.warning(f"Redis delete failed for {prompt_type}: {e}")
            return False

    def get_or_fetch(
        self,
        prompt_type: str,
        fetch_fn: Callable[[], Optional[str]],
    ) -> Optional[str]:
        """Get from cache or fetch and cache.

        Implements read-through caching pattern:
        1. Try to get from cache
        2. On miss, call fetch_fn to get from DB
        3. Cache the result

        Args:
            prompt_type: The type of prompt.
            fetch_fn: Function to call to fetch from DB on cache miss.

        Returns:
            Prompt content if found, None otherwise.
        """
        # Try cache first
        cached = self.get_cached_prompt(prompt_type)
        if cached is not None:
            return cached

        # Fetch from DB
        content = fetch_fn()
        if content is not None:
            self.set_cached_prompt(prompt_type, content)

        return content
