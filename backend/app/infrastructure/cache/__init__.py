from app.domain.recap.models import RecapCache
from app.infrastructure.cache.memory import InMemoryRecapCache
from app.infrastructure.cache.redis import RedisRecapCache
from config import Config


def get_recap_cache() -> RecapCache:
    fallback = InMemoryRecapCache()
    try:
        cache = RedisRecapCache(redis_url=Config.REDIS_URL, fallback=fallback)
        if cache.is_connected:
            return cache
    except Exception:
        pass
    return fallback


__all__ = ["InMemoryRecapCache", "RedisRecapCache", "get_recap_cache"]
