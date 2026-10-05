from redis import Redis

from app.config import settings

_redis: Redis | None = None


def get_redis() -> Redis:
    """Text-mode Redis connection for pub/sub, counters, and caching."""
    global _redis
    if _redis is None:
        _redis = Redis.from_url(settings.redis_url, decode_responses=True)
    return _redis