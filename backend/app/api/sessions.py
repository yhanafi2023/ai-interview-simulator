import logging
import uuid
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser
from app.db.session import get_db
from app.models import Answer, GradingJob, InterviewSession, Question, SessionQuestion
from app.models.user import User
from app.queue import get_queue
from app.schemas.interview import (
    CreateSessionRequest,
    GradingJobOut,
    SessionOut,
    SubmitAnswerRequest,
)
from app.schemas.question import QuestionOut
from app.tasks.grading import grade_answer_task
from fastapi import Header
from app.services.idempotency import claim, save_response, stored_response
from rq import Retry

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
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> GradingJobOut:
    scope = "submit-answer"

    if idempotency_key:
        replay = stored_response(str(user.id), scope, idempotency_key)
        if replay is not None:
            logger.info("replaying idempotent response for key %s", idempotency_key)
            return GradingJobOut.model_validate(replay)

        if not claim(str(user.id), scope, idempotency_key):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A request with this idempotency key is already in progress",
            )

    session = _owned_session(db, session_id, user)

    # ... all the existing validation and insert logic, unchanged ...

    db.commit()

    get_queue().enqueue(
        grade_answer_task,
        str(job.id),
        job_timeout=180,
        retry=Retry(max=2, interval=[10, 30]),
    )

    logger.info("queued grading job %s for answer %s", job.id, answer.id)

    result = GradingJobOut(
        id=job.id,
        answer_id=answer.id,
        question_id=body.question_id,
        status="queued",
    )

    if idempotency_key:
        save_response(
            str(user.id),
            scope,
            idempotency_key,
            result.model_dump(mode="json", by_alias=True),
        )

    return result