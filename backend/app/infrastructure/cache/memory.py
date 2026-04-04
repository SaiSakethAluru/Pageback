from __future__ import annotations

from app.domain.recap.models import RecapCache
from app.services import recap_cache


class InMemoryRecapCache(RecapCache):
    def get(self, cache_key: str) -> str | None:
        return recap_cache.get(cache_key)

    def set(self, cache_key: str, summary: str, ttl_seconds: int = 86400) -> None:
        recap_cache.set(cache_key, summary, ttl_seconds)

    def make_key(self, book_id: str, position_char: int, level: int) -> str:
        return recap_cache.make_key(book_id, position_char, level)

    def invalidate_book(self, book_id: str) -> None:
        recap_cache.invalidate_book(book_id)
