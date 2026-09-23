import logging

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


def grade_answer(*, prompt: str, answer: str, allow_llm: bool = True) -> GradingResult:
    if not allow_llm:
        return _grade_heuristic(answer)

    try:
        return grade_with_claude(question=prompt, answer=answer)
    except GradingUnavailable:
        logger.exception("llm grading unavailable, falling back to heuristic")
        return _grade_heuristic(answer)


__all__ = ["GRADING_PROMPT_VERSION", "GradingResult", "ScoreResult", "grade_answer"]