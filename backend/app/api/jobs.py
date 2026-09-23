import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser
from app.db.session import get_db
from app.models import Answer, Feedback, GradingJob, InterviewSession, Score
from app.schemas.interview import FeedbackOut, GradingJobOut, ScoreOut

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