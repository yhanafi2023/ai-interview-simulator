from redis import Redis
from rq import Queue

from app.config import settings

GRADING_QUEUE = "grading"

_rq_connection: Redis | None = None


def get_rq_connection() -> Redis:
    """Raw-bytes Redis connection for RQ.

    RQ stores pickled job payloads, so this connection must NOT use
    decode_responses — decoding would corrupt them.
    """
    global _rq_connection
    if _rq_connection is None:
        _rq_connection = Redis.from_url(settings.redis_url)
    return _rq_connection


def get_queue() -> Queue:
    return Queue(GRADING_QUEUE, connection=get_rq_connection())