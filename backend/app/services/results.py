from dataclasses import dataclass

HEURISTIC_VERSION = "v0-heuristic"


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