import logging
import time

logger = logging.getLogger(__name__)


def ping(message: str) -> str:
    logger.info("ping task started: %s", message)
    time.sleep(2)
    logger.info("ping task finished: %s", message)
    return f"pong: {message}"