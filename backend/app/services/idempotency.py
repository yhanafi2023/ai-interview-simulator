import json
import logging
from typing import Any

from app.redis_client import get_redis

IN_PROGRESS = "__in_progress__"
IN_PROGRESS_TTL = 60
RESPONSE_TTL = 24 * 60 * 60

logger = logging.getLogger(__name__)


def _redis_key(user_id: str, scope: str, client_key: str) -> str:
    return f"idem:{scope}:{user_id}:{client_key}"


def claim(user_id: str, scope: str, client_key: str) -> bool:
    """Reserve this key. Returns False if someone already holds it."""
    return bool(
        get_redis().set(
            _redis_key(user_id, scope, client_key),
            IN_PROGRESS,
            nx=True,
            ex=IN_PROGRESS_TTL,
        )
    )


def stored_response(user_id: str, scope: str, client_key: str) -> dict[str, Any] | None:
    raw = get_redis().get(_redis_key(user_id, scope, client_key))
    if raw is None or raw == IN_PROGRESS:
        return None
    try:
        return json.loads(raw)
    except ValueError:
        return None


def save_response(user_id: str, scope: str, client_key: str, payload: dict[str, Any]) -> None:
    get_redis().set(
        _redis_key(user_id, scope, client_key),
        json.dumps(payload),
        ex=RESPONSE_TTL,
    )