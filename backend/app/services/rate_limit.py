import logging
import time
from dataclasses import dataclass

from redis.exceptions import RedisError

from app.redis_client import get_redis

logger = logging.getLogger(__name__)

_TOKEN_BUCKET_LUA = """
local key = KEYS[1]
local capacity = tonumber(ARGV[1])
local refill_rate = tonumber(ARGV[2])
local now = tonumber(ARGV[3])
local cost = tonumber(ARGV[4])

local bucket = redis.call('HMGET', key, 'tokens', 'updated')
local tokens = tonumber(bucket[1])
local updated = tonumber(bucket[2])

if tokens == nil then
  tokens = capacity
  updated = now
end

local elapsed = math.max(0, now - updated)
tokens = math.min(capacity, tokens + elapsed * refill_rate)

local allowed = 0
if tokens >= cost then
  tokens = tokens - cost
  allowed = 1
end

redis.call('HSET', key, 'tokens', tokens, 'updated', now)
redis.call('EXPIRE', key, math.ceil(capacity / refill_rate) * 2)

return {allowed, tostring(tokens)}
"""

_script = None


@dataclass(frozen=True)
class RateLimitResult:
    allowed: bool
    tokens_remaining: float
    retry_after_seconds: int


def _get_script():  # noqa: ANN202
    global _script
    if _script is None:
        _script = get_redis().register_script(_TOKEN_BUCKET_LUA)
    return _script


def consume(
    key: str,
    *,
    capacity: int,
    refill_per_second: float,
    cost: int = 1,
) -> RateLimitResult:
    """Take one token from a bucket. Fails open if Redis is unavailable."""
    try:
        allowed, tokens = _get_script()(
            keys=[f"ratelimit:{key}"],
            args=[capacity, refill_per_second, time.time(), cost],
        )
    except RedisError:
        logger.warning("rate limiter unavailable, allowing request", exc_info=True)
        return RateLimitResult(True, float(capacity), 0)

    remaining = float(tokens)
    retry_after = 0 if allowed else max(1, int((cost - remaining) / refill_per_second))

    return RateLimitResult(bool(allowed), remaining, retry_after)