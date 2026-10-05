from typing import Annotated

from fastapi import APIRouter, Depends
from rq import Queue
from rq.registry import FailedJobRegistry
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import AdminUser
from app.db.session import get_db
from app.models import GradingJob
from app.queue import GRADING_QUEUE, get_rq_connection
from app.services.cache import stats as cache_stats

router = APIRouter(prefix="/metrics", tags=["metrics"])

DbSession = Annotated[Session, Depends(get_db)]


@router.get("")
def metrics(_admin: AdminUser, db: DbSession) -> dict:
    queue = Queue(GRADING_QUEUE, connection=get_rq_connection())

    job_counts = dict(
        db.execute(select(GradingJob.status, func.count()).group_by(GradingJob.status)).all()
    )

    return {
        "grade_cache": cache_stats(),
        "queue": {
            "pending": queue.count,
            "failed": FailedJobRegistry(queue=queue).count,
        },
        "jobs": {
            "queued": job_counts.get("queued", 0),
            "running": job_counts.get("running", 0),
            "succeeded": job_counts.get("succeeded", 0),
            "failed": job_counts.get("failed", 0),
        },
    }