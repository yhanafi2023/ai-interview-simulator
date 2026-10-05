import hashlib
import json
import logging
import re
from dataclasses import asdict

from app.redis_client import get_redis
from app.services.results import GradingResult, ScoreResult

logger = logging.getLogger(__name__)

CACHE_TTL_SECONDS = 30 * 24 * 60 * 60
HIT_COUNTER = "metrics:grade_cache:hits"
MISS_COUNTER = "metrics:grade_cache:misses"

_WHITESPACE = re.compile(r"\s+")


def _normalize(text: str) -> str:
    return _WHITESPACE.sub(" ", text.strip())


def cache_key(*, prompt_version: str, question_id: str, answer: str) -> str:
    payload = f"{prompt_version}|{question_id}|{_normalize(answer)}"
    digest = hashlib.sha256(payload.encode()).hexdigest()
    return f"grade:{prompt_version}:{digest}"


def _bump(counter: str) -> None:
    try:
        get_redis().incr(counter)
    except Exception:
        logger.debug("could not increment %s", counter, exc_info=True)


def get_cached(key: str) -> GradingResult | None:
    try:
        raw = get_redis().get(key)
    except Exception:
        logger.warning("grade cache read failed", exc_info=True)
        return None

    if raw is None:
        _bump(MISS_COUNTER)
        return None

    try:
        data = json.loads(raw)
        result = GradingResult(
            scores=[ScoreResult(**score) for score in data["scores"]],
            strengths=data["strengths"],
            improvements=data["improvements"],
            follow_up_question=data.get("follow_up_question"),
            prompt_version=data["prompt_version"],
        )
    except (ValueError, KeyError, TypeError):
        logger.warning("discarding malformed cache entry %s", key)
        return None

    _bump(HIT_COUNTER)
    return result


def set_cached(key: str, result: GradingResult) -> None:
    try:
        get_redis().set(key, json.dumps(asdict(result)), ex=CACHE_TTL_SECONDS)
    except Exception:
        logger.warning("grade cache write failed", exc_info=True)


def stats() -> dict[str, float]:
    redis = get_redis()
    hits = int(redis.get(HIT_COUNTER) or 0)
    misses = int(redis.get(MISS_COUNTER) or 0)
    total = hits + misses

    return {
        "hits": hits,
        "misses": misses,
        "total": total,
        "hit_rate": round(hits / total, 4) if total else 0.0,
    }