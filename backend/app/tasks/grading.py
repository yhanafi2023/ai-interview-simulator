import json
import logging
import uuid
from datetime import UTC, datetime

from app.db.session import SessionLocal
from app.models import Answer, Feedback, GradingJob, InterviewSession, Question, Score
from app.redis_client import get_redis
from app.services.budget import llm_allowed
from app.services.grading import grade_answer

logger = logging.getLogger(__name__)


def _publish(job_id: str, payload: dict) -> None:
    try:
        get_redis().publish(f"grading:{job_id}", json.dumps(payload))
    except Exception:
        logger.warning("failed to publish progress for job %s", job_id, exc_info=True)


def grade_answer_task(job_id: str) -> None:
    """Grade one answer. Runs in the worker process, not the API."""
    db = SessionLocal()
    try:
        job = db.get(GradingJob, uuid.UUID(job_id))
        if job is None:
            logger.error("grading job %s not found", job_id)
            return

        if job.status in {"succeeded", "failed"}:
            logger.info("grading job %s already %s, skipping", job_id, job.status)
            return

        answer = db.get(Answer, job.answer_id)
        if answer is None:
            job.status = "failed"
            job.error = "answer not found"
            job.finished_at = datetime.now(UTC)
            db.commit()
            return

        question = db.get(Question, answer.question_id)
        session = db.get(InterviewSession, answer.session_id)

        job.status = "running"
        job.attempts += 1
        job.started_at = datetime.now(UTC)
        db.commit()
        _publish(job_id, {"status": "running"})

        allowed, reason = llm_allowed(db, session.user_id)
        if not allowed:
            logger.info("llm grading skipped for job %s: %s", job_id, reason)

        result = grade_answer(
            prompt=question.prompt,
            answer=answer.content,
            allow_llm=allowed,
        )

        feedback = Feedback(
            answer_id=answer.id,
            strengths=result.strengths,
            improvements=result.improvements,
            follow_up_question=result.follow_up_question,
            prompt_version=result.prompt_version,
        )
        db.add(feedback)
        db.flush()

        for score in result.scores:
            db.add(
                Score(
                    feedback_id=feedback.id,
                    dimension=score.dimension,
                    value=score.value,
                    justification=score.justification,
                )
            )

        job.status = "succeeded"
        job.finished_at = datetime.now(UTC)
        db.commit()

        logger.info("grading job %s succeeded (%s)", job_id, result.prompt_version)
        _publish(job_id, {"status": "succeeded"})

    except Exception as exc:
        logger.exception("grading job %s failed", job_id)
        db.rollback()
        try:
            job = db.get(GradingJob, uuid.UUID(job_id))
            if job is not None:
                job.status = "failed"
                job.error = f"{type(exc).__name__}: {exc}"[:2000]
                job.finished_at = datetime.now(UTC)
                db.commit()
        except Exception:
            logger.exception("could not record failure for job %s", job_id)
        _publish(job_id, {"status": "failed"})
        raise
    finally:
        db.close()