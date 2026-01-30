"""
Integration tests for prompt caching with Redis.

Tests that active prompts are cached and invalidated on publish.
"""
import os
import pytest
from unittest.mock import MagicMock

# Set required environment variables BEFORE importing app
os.environ['APP_NAME'] = 'TestApp'
os.environ['BOT_NAME'] = 'TestBot'
os.environ['DATABASE_URL'] = 'sqlite:///:memory:?cache=shared'
os.environ['API_KEY'] = 'test-api-key'
os.environ['REDIS_URL'] = 'redis://localhost:6379'

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from database.connection import Base
from database.models import PromptTemplate, PromptVersion


class TestPromptCacheService:
    """Test suite for PromptCacheService."""

    @pytest.fixture
    def db_session(self):
        """Create isolated database session."""
        engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(bind=engine)
        Session = sessionmaker(bind=engine)
        session = Session()
        yield session
        session.close()

    def test_get_cached_prompt_returns_none_when_not_cached(self, db_session):
        """Test that get returns None when prompt not in cache."""
        from services.prompt_cache import PromptCacheService

        mock_redis = MagicMock()
        mock_redis.get.return_value = None

        cache = PromptCacheService(redis_client=mock_redis)
        result = cache.get_cached_prompt("system_prompt")

        assert result is None
        mock_redis.get.assert_called_once_with("prompt:system_prompt")

    def test_get_cached_prompt_returns_content_when_cached(self, db_session):
        """Test that get returns cached content."""
        from services.prompt_cache import PromptCacheService

        mock_redis = MagicMock()
        mock_redis.get.return_value = b"Cached prompt content"

        cache = PromptCacheService(redis_client=mock_redis)
        result = cache.get_cached_prompt("system_prompt")

        assert result == "Cached prompt content"

    def test_set_cached_prompt_stores_with_ttl(self, db_session):
        """Test that set stores prompt with correct TTL."""
        from services.prompt_cache import PromptCacheService

        mock_redis = MagicMock()
        cache = PromptCacheService(redis_client=mock_redis)

        cache.set_cached_prompt("system_prompt", "Content to cache")

        mock_redis.setex.assert_called_once()
        call_args = mock_redis.setex.call_args
        assert call_args[0][0] == "prompt:system_prompt"
        assert call_args[0][1] == 3600  # 1 hour TTL
        assert call_args[0][2] == "Content to cache"

    def test_invalidate_prompt_deletes_cache_key(self, db_session):
        """Test that invalidate deletes the cache key."""
        from services.prompt_cache import PromptCacheService

        mock_redis = MagicMock()
        cache = PromptCacheService(redis_client=mock_redis)

        cache.invalidate_prompt("system_prompt")

        mock_redis.delete.assert_called_once_with("prompt:system_prompt")

    def test_get_or_fetch_returns_cached_value(self, db_session):
        """Test that get_or_fetch returns cached value if available."""
        from services.prompt_cache import PromptCacheService

        mock_redis = MagicMock()
        mock_redis.get.return_value = b"Cached content"

        cache = PromptCacheService(redis_client=mock_redis)
        fetch_fn = MagicMock(return_value="DB content")

        result = cache.get_or_fetch("system_prompt", fetch_fn)

        assert result == "Cached content"
        fetch_fn.assert_not_called()  # Should not fetch from DB

    def test_get_or_fetch_fetches_and_caches_on_miss(self, db_session):
        """Test that get_or_fetch fetches and caches on cache miss."""
        from services.prompt_cache import PromptCacheService

        mock_redis = MagicMock()
        mock_redis.get.return_value = None  # Cache miss

        cache = PromptCacheService(redis_client=mock_redis)
        fetch_fn = MagicMock(return_value="DB content")

        result = cache.get_or_fetch("system_prompt", fetch_fn)

        assert result == "DB content"
        fetch_fn.assert_called_once()
        mock_redis.setex.assert_called_once()  # Should cache the result


class TestPromptServiceWithCache:
    """Test suite for PromptService with cache integration."""

    @pytest.fixture
    def db_session(self):
        """Create isolated database session."""
        engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(bind=engine)
        Session = sessionmaker(bind=engine)
        session = Session()
        yield session
        session.close()

    def test_get_active_content_with_cache_uses_cache(self, db_session):
        """Test that get_active_content uses cache when available."""
        from services.prompt_service import PromptService
        from services.prompt_cache import PromptCacheService

        service = PromptService(db_session)

        # Create a prompt first
        template = service.create_template(
            name="test_prompt",
            prompt_type="system_prompt",
            content="Original content"
        )

        # Mock cache that returns cached content
        mock_redis = MagicMock()
        mock_redis.get.return_value = b"Cached content"
        cache = PromptCacheService(redis_client=mock_redis)

        # Get with cache
        result = service.get_active_content_with_cache("test_prompt", cache)

        assert result == "Cached content"
        mock_redis.get.assert_called()

    def test_get_active_content_with_cache_fetches_on_miss(self, db_session):
        """Test that get_active_content fetches from DB on cache miss."""
        from services.prompt_service import PromptService
        from services.prompt_cache import PromptCacheService

        service = PromptService(db_session)

        # Create a prompt first
        service.create_template(
            name="test_prompt",
            prompt_type="system_prompt",
            content="DB content"
        )

        # Mock cache with cache miss
        mock_redis = MagicMock()
        mock_redis.get.return_value = None  # Cache miss
        cache = PromptCacheService(redis_client=mock_redis)

        # Get with cache
        result = service.get_active_content_with_cache("test_prompt", cache)

        assert result == "DB content"
        mock_redis.setex.assert_called_once()  # Should cache the result

    def test_publish_version_invalidates_cache(self, db_session):
        """Test that publishing a version invalidates the cache."""
        from services.prompt_service import PromptService
        from services.prompt_cache import PromptCacheService

        service = PromptService(db_session)

        # Create a prompt with two versions
        template = service.create_template(
            name="test_prompt",
            prompt_type="system_prompt",
            content="Version 1"
        )
        service.update_template(
            template.id,
            edit_version=template.edit_version,
            content="Version 2"
        )

        # Mock cache
        mock_redis = MagicMock()
        cache = PromptCacheService(redis_client=mock_redis)

        # Publish version 1
        service.publish_version_with_cache(template.id, 1, cache)

        # Should invalidate cache
        mock_redis.delete.assert_called_with("prompt:system_prompt")


class TestCacheKeyPattern:
    """Test suite for cache key patterns."""

    def test_cache_key_uses_prompt_type(self):
        """Test that cache key is based on prompt type."""
        from services.prompt_cache import PromptCacheService

        assert PromptCacheService.get_cache_key("system_prompt") == "prompt:system_prompt"
        assert PromptCacheService.get_cache_key("greeting") == "prompt:greeting"
        assert PromptCacheService.get_cache_key("retrieval") == "prompt:retrieval"

    def test_cache_ttl_is_one_hour(self):
        """Test that cache TTL is 3600 seconds (1 hour)."""
        from services.prompt_cache import PromptCacheService

        assert PromptCacheService.CACHE_TTL == 3600
