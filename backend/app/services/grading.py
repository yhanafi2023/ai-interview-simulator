from dataclasses import dataclass


@dataclass(frozen=True)
class ScoreResult:
    dimension: str
    value: int
    justification: str


@dataclass(frozen=True)
class GradingResult:
    scores: list[ScoreResult]
    strengths: list[str]
    improvements: list[str]
    follow_up_question: str | None
    prompt_version: str


def grade_answer(*, prompt: str, answer: str) -> GradingResult:
    
    length = len(answer.strip())
    base = 8 if length > 400 else 6 if length > 150 else 4

    return GradingResult(
        scores=[
            ScoreResult("correctness", base, "The core approach is sound but skips a key constraint."),
            ScoreResult("communication", min(10, base + 1), "Clear structure. State your assumptions earlier."),
            ScoreResult("depth", max(1, base - 1), "Complexity is mentioned but not derived."),
            ScoreResult("edge_cases", max(1, base - 2), "Empty and single-element inputs are not addressed."),
        ],
        strengths=[
            "You explained your approach before writing code.",
            "Variable naming was clear and consistent.",
        ],
        improvements=[
            "Walk through at least one edge case out loud.",
            "Give the time and space complexity explicitly.",
        ],
        follow_up_question=(
            "How would your solution change if the input did not fit in memory?"
            if length > 150
            else None
        ),
        prompt_version="v0-heuristic",
    )