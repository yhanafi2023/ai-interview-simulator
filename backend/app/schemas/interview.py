import uuid
from datetime import datetime
from typing import Literal

from pydantic import Field

from app.schemas.base import CamelModel
from app.schemas.question import Difficulty, InterviewType, QuestionOut

SessionStatus = Literal["in_progress", "completed"]
ScoreDimension = Literal["correctness", "communication", "depth", "edge_cases"]


class CreateSessionRequest(CamelModel):
    type: InterviewType
    difficulty: Difficulty
    question_count: int = Field(ge=1, le=10)


class SessionOut(CamelModel):
    id: uuid.UUID
    type: InterviewType
    difficulty: Difficulty
    status: SessionStatus
    created_at: datetime
    questions: list[QuestionOut]


class SubmitAnswerRequest(CamelModel):
    question_id: uuid.UUID
    content: str = Field(min_length=1)


class ScoreOut(CamelModel):
    dimension: ScoreDimension
    value: int = Field(ge=0, le=10)
    justification: str


class FeedbackOut(CamelModel):
    answer_id: uuid.UUID
    question_id: uuid.UUID
    scores: list[ScoreOut]
    strengths: list[str]
    improvements: list[str]
    follow_up_question: str | None = None
