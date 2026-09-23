import logging

from rq import Queue, Worker

from app.queue import GRADING_QUEUE, get_rq_connection

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s | %(message)s",
)

logger = logging.getLogger(__name__)


def main() -> None:
    connection = get_rq_connection()
    queues = [Queue(GRADING_QUEUE, connection=connection)]
    logger.info("worker starting, listening on %s", GRADING_QUEUE)
    Worker(queues, connection=connection).work()


if __name__ == "__main__":
    main()