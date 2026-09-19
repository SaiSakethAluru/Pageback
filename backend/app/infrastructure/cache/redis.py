from __future__ import annotations

import logging

import redis

from app.domain.recap.models import RecapCache
from config import Config

logger = logging.getLogger(__name__)


class RedisRecapCache(RecapCache):
    def __init__(
        self,
        redis_url: str | None = None,
        fallback: RecapCache | None = None,
        default_ttl_seconds: int = 86400,
    ) -> None:
        self._url = redis_url or Config.REDIS_URL
        self._fallback = fallback
        self._ttl_seconds = default_ttl_seconds
        self._client: redis.Redis | None = None
        self._connect()

    def _connect(self) -> None:
        try:
            client = redis.Redis.from_url(self._url, decode_responses=True)
            client.ping()
            self._client = client
            logger.info("Connected to Redis recap cache at %s", self._url)
        except Exception as exc:
            logger.warning(
                "Redis recap cache unavailable (%s). Falling back to in-memory cache.",
                exc,
            )
            self._client = None

    @property
    def is_connected(self) -> bool:
        return self._client is not None

    def get(self, cache_key: str) -> str | None:
        if self._client is not None:
            try:
                val = self._client.get(cache_key)
                if val is not None:
                    return str(val)
                return None
            except Exception as exc:
                logger.warning("Redis GET failed for %s: %s", cache_key, exc)
        if self._fallback is not None:
            return self._fallback.get(cache_key)
        return None

    def set(self, cache_key: str, summary: str, ttl_seconds: int | None = None) -> None:
        ttl = ttl_seconds if ttl_seconds is not None else self._ttl_seconds
        if self._client is not None:
            try:
                self._client.set(cache_key, summary, ex=ttl)
            except Exception as exc:
                logger.warning("Redis SET failed for %s: %s", cache_key, exc)
        if self._fallback is not None:
            self._fallback.set(cache_key, summary, ttl_seconds=ttl)

    def make_key(self, book_id: str, position_char: int, level: int) -> str:
        return f"recap:{book_id}:{position_char}:{level}"

    def invalidate_book(self, book_id: str) -> None:
        if self._client is not None:
            try:
                pattern = f"recap:{book_id}:*"
                cursor = 0
                while True:
                    cursor, keys = self._client.scan(cursor=cursor, match=pattern, count=100)
                    if keys:
                        self._client.delete(*keys)
                    if cursor == 0:
                        break
            except Exception as exc:
                logger.warning("Redis invalidate failed for book %s: %s", book_id, exc)
        if self._fallback is not None:
            self._fallback.invalidate_book(book_id)
