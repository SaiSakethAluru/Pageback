from __future__ import annotations

import hashlib
from datetime import datetime, timedelta

_cache: dict[str, dict[str, object]] = {}
_book_index: dict[str, set[str]] = {}

DEFAULT_TTL_SECONDS = 86400


def get(cache_key: str) -> str | None:
    entry = _cache.get(cache_key)
    if not entry:
        return None

    expires_at = entry["expires_at"]
    if isinstance(expires_at, datetime) and expires_at <= datetime.now():
        _cache.pop(cache_key, None)
        return None

    return str(entry["summary"])


def set(cache_key: str, summary: str, ttl_seconds: int = DEFAULT_TTL_SECONDS) -> None:
    _cache[cache_key] = {
        "summary": summary,
        "expires_at": datetime.now() + timedelta(seconds=ttl_seconds),
    }


def make_key(book_id: str, position_char: int, level: int) -> str:
    raw = f"{book_id}:{position_char}:{level}"
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    _book_index.setdefault(book_id, set()).add(digest)
    return digest


def invalidate_book(book_id: str) -> None:
    keys = _book_index.pop(book_id, set())
    for cache_key in keys:
        _cache.pop(cache_key, None)
    # TODO: when migrating to Redis, use key prefix pattern to handle this.
