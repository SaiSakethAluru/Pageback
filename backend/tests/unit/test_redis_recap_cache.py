from unittest.mock import MagicMock

from app.domain.recap.models import RecapCache
from app.infrastructure.cache.memory import InMemoryRecapCache
from app.infrastructure.cache.redis import RedisRecapCache


class DummyFallbackCache(RecapCache):
    def __init__(self):
        self.store = {}

    def get(self, cache_key: str) -> str | None:
        return self.store.get(cache_key)

    def set(self, cache_key: str, summary: str, ttl_seconds: int = 86400) -> None:
        self.store[cache_key] = summary

    def make_key(self, book_id: str, position_char: int, level: int) -> str:
        return f"{book_id}:{position_char}:{level}"

    def invalidate_book(self, book_id: str) -> None:
        self.store = {k: v for k, v in self.store.items() if not k.startswith(book_id)}


def test_redis_cache_make_key():
    cache = RedisRecapCache(redis_url="redis://dummy:6379/0")
    key = cache.make_key("book-123", 5000, 2)
    assert key == "recap:book-123:5000:2"


def test_redis_cache_set_and_get():
    mock_redis = MagicMock()
    mock_redis.get.return_value = "Cached recap content"

    cache = RedisRecapCache(redis_url="redis://dummy:6379/0")
    cache._client = mock_redis

    cache.set("recap:book:100:1", "Cached recap content", ttl_seconds=3600)
    mock_redis.set.assert_called_once_with("recap:book:100:1", "Cached recap content", ex=3600)

    result = cache.get("recap:book:100:1")
    assert result == "Cached recap content"
    mock_redis.get.assert_called_once_with("recap:book:100:1")


def test_redis_cache_fallback_when_unconnected():
    fallback = DummyFallbackCache()
    cache = RedisRecapCache(redis_url="redis://invalid-host:6379/0", fallback=fallback)
    # Ensure client is None
    cache._client = None

    cache.set("recap:book:100:1", "Fallback summary", ttl_seconds=60)
    assert fallback.get("recap:book:100:1") == "Fallback summary"
    assert cache.get("recap:book:100:1") == "Fallback summary"


def test_redis_cache_invalidate_book():
    mock_redis = MagicMock()
    mock_redis.scan.side_effect = [
        (42, ["recap:book-1:100:1", "recap:book-1:200:2"]),
        (0, ["recap:book-1:300:3"]),
    ]

    cache = RedisRecapCache(redis_url="redis://dummy:6379/0")
    cache._client = mock_redis

    cache.invalidate_book("book-1")
    assert mock_redis.delete.call_count == 2
