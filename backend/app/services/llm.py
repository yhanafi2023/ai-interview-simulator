import logging
import random
import time
from typing import Any

import anthropic
from pydantic import BaseModel, Field, ValidationError

from app.config import settings
from app.services.prompts import (
    GRADING_PROMPT_VERSION,
    GRADING_SYSTEM_PROMPT,
    build_grading_message,
)
from app.services.results import GradingResult, ScoreResult

logger = logging.getLogger(__name__)

DIMENSIONS = ["correctness", "communication", "depth", "edge_cases"]

GRADING_TOOL: dict[str, Any] = {
    "name": "submit_grade",
    "description": "Submit a structured evaluation of a candidate's interview answer.",
    "input_schema": {
        "type": "object",
        "properties": {
            "scores": {
                "type": "array",
                "minItems": 4,
                "maxItems": 4,
                "items": {
                    "type": "object",
                    "properties": {
                        "dimension": {"type": "string", "enum": DIMENSIONS},
                        "value": {"type": "integer", "minimum": 0, "maximum": 10},
                        "justification": {"type": "string"},
                    },
                    "required": ["dimension", "value", "justification"],
                },
            },
            "strengths": {
                "type": "array",
                "minItems": 1,
                "maxItems": 4,
                "items": {"type": "string"},
            },
            "improvements": {
                "type": "array",
                "minItems": 1,
                "maxItems": 4,
                "items": {"type": "string"},
            },
            "follow_up_question": {
                "type": "string",
                "description": "Omit entirely if there is nothing specific worth probing.",
            },
        },
        "required": ["scores", "strengths", "improvements"],
    },
}


class GradingUnavailable(RuntimeError):
    """The model could not produce a usable grade."""


class _ScorePayload(BaseModel):
    dimension: str
    value: int = Field(ge=0, le=10)
    justification: str


class _GradePayload(BaseModel):
    scores: list[_ScorePayload]
    strengths: list[str]
    improvements: list[str]
    follow_up_question: str | None = None


_client: anthropic.Anthropic | None = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(
            api_key=settings.anthropic_api_key,
            timeout=settings.anthropic_timeout_seconds,
            max_retries=0,
        )
    return _client


def _call_model(*, question: str, answer: str) -> anthropic.types.Message:
    retryable = (
        anthropic.APIConnectionError,
        anthropic.APITimeoutError,
        anthropic.RateLimitError,
        anthropic.InternalServerError,
    )

    for attempt in range(settings.anthropic_max_retries):
        try:
            return _get_client().messages.create(
                model=settings.anthropic_model,
                max_tokens=settings.anthropic_max_tokens,
                system=GRADING_SYSTEM_PROMPT,
                tools=[GRADING_TOOL],
                tool_choice={"type": "tool", "name": "submit_grade"},
                messages=[
                    {
                        "role": "user",
                        "content": build_grading_message(question=question, answer=answer),
                    }
                ],
            )
        except retryable as exc:
            if attempt == settings.anthropic_max_retries - 1:
                raise GradingUnavailable(f"{type(exc).__name__}: {exc}") from exc

            delay = 2**attempt + random.uniform(0, 1)
            logger.warning(
                "grading attempt %d failed (%s), retrying in %.1fs",
                attempt + 1,
                type(exc).__name__,
                delay,
            )
            time.sleep(delay)

    raise GradingUnavailable("exhausted retries")


def grade_with_claude(*, question: str, answer: str) -> GradingResult:
    response = _call_model(question=question, answer=answer)

    logger.info(
        "llm_grade model=%s input_tokens=%d output_tokens=%d stop=%s",
        settings.anthropic_model,
        response.usage.input_tokens,
        response.usage.output_tokens,
        response.stop_reason,
    )

    block = next((b for b in response.content if b.type == "tool_use"), None)
    if block is None:
        raise GradingUnavailable("model did not call the grading tool")

    try:
        payload = _GradePayload.model_validate(block.input)
    except ValidationError as exc:
        raise GradingUnavailable(f"tool payload failed validation: {exc}") from exc

    by_dimension = {s.dimension: s for s in payload.scores}
    missing = [d for d in DIMENSIONS if d not in by_dimension]
    if missing:
        raise GradingUnavailable(f"missing dimensions: {missing}")

    return GradingResult(
        scores=[
            ScoreResult(
                dimension=d,
                value=by_dimension[d].value,
                justification=by_dimension[d].justification,
            )
            for d in DIMENSIONS
        ],
        strengths=payload.strengths,
        improvements=payload.improvements,
        follow_up_question=payload.follow_up_question,
        prompt_version=GRADING_PROMPT_VERSION,
    )