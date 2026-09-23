import logging
import uuid
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser
from app.db.session import get_db
from app.models import Answer, Feedback, InterviewSession, Question, Score, SessionQuestion
from app.models.user import User
from app.models import (
    Answer,
    GradingJob,
    InterviewSession,
    Question,
    SessionQuestion,
)
from app.queue import get_queue
from app.schemas.interview import (
    CreateSessionRequest,
    GradingJobOut,
    SessionOut,
    SubmitAnswerRequest,
)
from app.tasks.grading import grade_answer_task

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sessions", tags=["sessions"])

DbSession = Annotated[Session, Depends(get_db)]


def _serialize(session: InterviewSession) -> SessionOut:
    return SessionOut(
        id=session.id,
        type=session.type,
        difficulty=session.difficulty,
        status=session.status,
        created_at=session.created_at,
        questions=[QuestionOut.model_validate(sq.question) for sq in session.session_questions],
    )


def _owned_session(db: Session, session_id: uuid.UUID, user: User) -> InterviewSession:
    session = db.get(InterviewSession, session_id)
    if session is None or session.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return session


@router.post("", response_model=SessionOut, status_code=status.HTTP_201_CREATED)
def create_session(body: CreateSessionRequest, user: CurrentUser, db: DbSession) -> SessionOut:
    picked = (
        db.execute(
            select(Question)
            .where(Question.type == body.type, Question.difficulty == body.difficulty)
            .order_by(func.random())
            .limit(body.question_count)
        )
        .scalars()
        .all()
    )

    if not picked:
        picked = (
            db.execute(
                select(Question)
                .where(Question.type == body.type)
                .order_by(func.random())
                .limit(body.question_count)
            )
            .scalars()
            .all()
        )

    if not picked:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No questions available for that interview type",
        )

    session = InterviewSession(
        user_id=user.id,
        type=body.type,
        difficulty=body.difficulty,
    )
    db.add(session)
    db.flush()

    for position, question in enumerate(picked, start=1):
        db.add(SessionQuestion(session_id=session.id, question_id=question.id, position=position))

    db.commit()
    db.refresh(session)

    return _serialize(session)


@router.get("/{session_id}", response_model=SessionOut)
def get_session(session_id: uuid.UUID, user: CurrentUser, db: DbSession) -> SessionOut:
    return _serialize(_owned_session(db, session_id, user))


@router.post(
    "/{session_id}/answers",
    response_model=GradingJobOut,
    status_code=status.HTTP_202_ACCEPTED,
)
def submit_answer(
    session_id: uuid.UUID,
    body: SubmitAnswerRequest,
    user: CurrentUser,
    db: DbSession,
) -> GradingJobOut:
    session = _owned_session(db, session_id, user)

    if session.status != "in_progress":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="This session is already complete"
        )

    in_session = db.execute(
        select(SessionQuestion).where(
            SessionQuestion.session_id == session.id,
            SessionQuestion.question_id == body.question_id,
        )
    ).scalar_one_or_none()

    if in_session is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="That question is not part of this session",
        )

    already = db.execute(
        select(Answer).where(
            Answer.session_id == session.id,
            Answer.question_id == body.question_id,
        )
    ).scalar_one_or_none()

    if already is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You have already answered this question",
        )

    answer = Answer(
        session_id=session.id,
        question_id=body.question_id,
        content=body.content,
    )
    db.add(answer)
    db.flush()

    job = GradingJob(answer_id=answer.id)
    db.add(job)

    answered = db.execute(
        select(func.count()).select_from(Answer).where(Answer.session_id == session.id)
    ).scalar_one()

    if answered >= len(session.session_questions):
        session.status = "completed"
        session.completed_at = datetime.now(UTC)

    db.commit()

    get_queue().enqueue(grade_answer_task, str(job.id), job_timeout=180)

    logger.info("queued grading job %s for answer %s", job.id, answer.id)

    return GradingJobOut(
        id=job.id,
        answer_id=answer.id,
        question_id=body.question_id,
        status="queued",
    )