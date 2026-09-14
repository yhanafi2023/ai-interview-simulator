from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Question
from app.schemas.question import (
    Difficulty,
    InterviewType,
    QuestionListResponse,
    QuestionOut,
)

router = APIRouter(prefix="/questions", tags=["questions"])


@router.get("", response_model=QuestionListResponse)
def list_questions(
    db: Annotated[Session, Depends(get_db)],
    type: InterviewType | None = None,
    difficulty: Difficulty | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> QuestionListResponse:
    stmt = select(Question)
    count_stmt = select(func.count()).select_from(Question)

    if type is not None:
        stmt = stmt.where(Question.type == type)
        count_stmt = count_stmt.where(Question.type == type)

    if difficulty is not None:
        stmt = stmt.where(Question.difficulty == difficulty)
        count_stmt = count_stmt.where(Question.difficulty == difficulty)

    total = db.execute(count_stmt).scalar_one()
    rows = db.execute(stmt.limit(limit)).scalars().all()

    return QuestionListResponse(
        items=[QuestionOut.model_validate(row) for row in rows],
        total=total,
    )