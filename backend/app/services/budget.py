import logging
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import settings
from app.models import Feedback
from app.services.results import HEURISTIC_VERSION

logger = logging.getLogger(__name__)


def _window_start() -> datetime:
    return datetime.now(UTC) - timedelta(days=1)


def _global_calls() -> Any:  # noqa: ANN401
    return (
        select(func.count())
        .select_from(Feedback)
        .where(
            Feedback.created_at >= _window_start(),
            Feedback.prompt_version != HEURISTIC_VERSION,
        )
    )


def llm_allowed(db: Session, user_id: uuid.UUID) -> tuple[bool, str | None]:
    """Global cost ceiling. Per-user fairness is handled by the rate limiter."""
    if not settings.anthropic_api_key:
        return False, "no api key configured"

    global_calls = db.execute(_global_calls()).scalar_one()
    if global_calls >= settings.llm_daily_call_budget:
        return False, f"global 24h budget reached ({global_calls})"

    return True, None