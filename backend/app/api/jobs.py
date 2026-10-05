import json
import time
import uuid
from collections.abc import Iterator
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from rq import Queue
from rq.registry import FailedJobRegistry
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import AdminUser, CurrentUser
from app.db.session import get_db
from app.models import Answer, Feedback, GradingJob, InterviewSession, Score
from app.queue import GRADING_QUEUE, get_rq_connection
from app.redis_client import get_redis
from app.schemas.interview import FeedbackOut, GradingJobOut, ScoreOut

TERMINAL = {"succeeded", "failed"}
STREAM_TIMEOUT_SECONDS = 180

router = APIRouter(prefix="/jobs", tags=["jobs"])

DbSession = Annotated[Session, Depends(get_db)]


def _load_owned_job(db: Session, job_id: uuid.UUID, user_id: uuid.UUID) -> tuple[GradingJob, Answer]:
    row = db.execute(
        select(GradingJob, Answer)
        .join(Answer, Answer.id == GradingJob.answer_id)
        .join(InterviewSession, InterviewSession.id == Answer.session_id)
        .where(GradingJob.id == job_id, InterviewSession.user_id == user_id)
    ).one_or_none()

    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    return row[0], row[1]


def serialize_job(db: Session, job: GradingJob, answer: Answer) -> GradingJobOut:
    feedback_out: FeedbackOut | None = None

    if job.status == "succeeded":
        feedback = db.execute(
            select(Feedback).where(Feedback.answer_id == answer.id)
        ).scalar_one_or_none()

        if feedback is not None:
            scores = db.execute(
                select(Score).where(Score.feedback_id == feedback.id)
            ).scalars().all()

            feedback_out = FeedbackOut(
                answer_id=answer.id,
                question_id=answer.question_id,
                scores=[
                    ScoreOut(
                        dimension=s.dimension, value=s.value, justification=s.justification
                    )
                    for s in scores
                ],
                strengths=feedback.strengths,
                improvements=feedback.improvements,
                follow_up_question=feedback.follow_up_question,
            )

    return GradingJobOut(
        id=job.id,
        answer_id=answer.id,
        question_id=answer.question_id,
        status=job.status,
        error=job.error,
        feedback=feedback_out,
    )


@router.get("/{job_id}", response_model=GradingJobOut)
def get_job(job_id: uuid.UUID, user: CurrentUser, db: DbSession) -> GradingJobOut:
    job, answer = _load_owned_job(db, job_id, user.id)
    return serialize_job(db, job, answer)
@router.get("/{job_id}/stream")
def stream_job(job_id: uuid.UUID, user: CurrentUser, db: DbSession) -> StreamingResponse:
    job, _answer = _load_owned_job(db, job_id, user.id)
    initial_status = job.status

    def events() -> Iterator[str]:
        yield f"data: {json.dumps({'status': initial_status})}\n\n"

        if initial_status in TERMINAL:
            return

        pubsub = get_redis().pubsub()
        pubsub.subscribe(f"grading:{job_id}")
        deadline = time.monotonic() + STREAM_TIMEOUT_SECONDS

        try:
            while time.monotonic() < deadline:
                message = pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)

                if message is None:
                    yield ": keep-alive\n\n"
                    continue

                data = message["data"]
                yield f"data: {data}\n\n"

                try:
                    if json.loads(data).get("status") in TERMINAL:
                        return
                except (ValueError, AttributeError):
                    continue
        finally:
            pubsub.close()

    return StreamingResponse(
        events(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
@router.get("/stats/queue")
def queue_stats(_admin: AdminUser, db: DbSession) -> dict[str, int]:
    connection = get_rq_connection()
    queue = Queue(GRADING_QUEUE, connection=connection)

    counts = dict(
        db.execute(
            select(GradingJob.status, func.count()).group_by(GradingJob.status)
        ).all()
    )

    return {
        "queued_in_redis": queue.count,
        "failed_in_redis": FailedJobRegistry(queue=queue).count,
        "db_queued": counts.get("queued", 0),
        "db_running": counts.get("running", 0),
        "db_succeeded": counts.get("succeeded", 0),
        "db_failed": counts.get("failed", 0),
    }