import logging

from app.services.cache import cache_key, get_cached, set_cached
from app.services.llm import GradingUnavailable, grade_with_claude
from app.services.prompts import GRADING_PROMPT_VERSION
from app.services.results import HEURISTIC_VERSION, GradingResult, ScoreResult

logger = logging.getLogger(__name__)


def _grade_heuristic(answer: str) -> GradingResult:
    length = len(answer.strip())
    base = 8 if length > 400 else 6 if length > 150 else 4

    return GradingResult(
        scores=[
            ScoreResult("correctness", base, "Automated fallback: scored on answer length."),
            ScoreResult("communication", min(10, base + 1), "Automated fallback."),
            ScoreResult("depth", max(1, base - 1), "Automated fallback."),
            ScoreResult("edge_cases", max(1, base - 2), "Automated fallback."),
        ],
        strengths=["Your answer was recorded."],
        improvements=["Detailed AI feedback was unavailable for this answer."],
        follow_up_question=None,
        prompt_version=HEURISTIC_VERSION,
    )


def grade_answer(
    *,
    prompt: str,
    answer: str,
    question_id: str = "",
    allow_llm: bool = True,
) -> GradingResult:
    key = cache_key(
        prompt_version=GRADING_PROMPT_VERSION,
        question_id=question_id,
        answer=answer,
    )

    cached = get_cached(key)
    if cached is not None:
        logger.info("grade cache hit for question %s", question_id)
        return cached

    if not allow_llm:
        return _grade_heuristic(answer)

    try:
        result = grade_with_claude(question=prompt, answer=answer)
    except GradingUnavailable:
        logger.exception("llm grading unavailable, falling back to heuristic")
        return _grade_heuristic(answer)

    set_cached(key, result)
    return result


__all__ = ["GRADING_PROMPT_VERSION", "GradingResult", "ScoreResult", "grade_answer"]