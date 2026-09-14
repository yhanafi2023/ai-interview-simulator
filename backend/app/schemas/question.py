import uuid
from typing import Literal

from app.schemas.base import CamelModel

InterviewType = Literal["technical", "behavioral", "system_design"]
Difficulty = Literal["easy", "medium", "hard"]


class QuestionOut(CamelModel):
    id: uuid.UUID
    type: InterviewType
    difficulty: Difficulty
    prompt: str


class QuestionListResponse(CamelModel):
    items: list[QuestionOut]
    total: int