import logging
from contextvars import ContextVar
from typing import Any

import sentry_sdk
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.integrations.rq import RqIntegration

from app.config import settings

logger = logging.getLogger(__name__)

request_id_var: ContextVar[str] = ContextVar("request_id", default="-")

_REDACT_HEADERS = {"authorization", "cookie", "set-cookie", "x-api-key"}


def _scrub(event: dict[str, Any], _hint: dict[str, Any]) -> dict[str, Any] | None:
    request = event.get("request") or {}

    headers = request.get("headers") or {}
    for name in list(headers):
        if name.lower() in _REDACT_HEADERS:
            headers[name] = "[redacted]"

    # Interview answers are user content. Never ship request bodies.
    request.pop("data", None)

    event.setdefault("tags", {}).setdefault("request_id", request_id_var.get())
    return event


def init_sentry(*, include_rq: bool = False) -> None:
    if not settings.sentry_dsn:
        logger.info("sentry disabled (no DSN configured)")
        return

    integrations = [
        LoggingIntegration(level=logging.INFO, event_level=logging.ERROR),
    ]
    if include_rq:
        integrations.append(RqIntegration())

    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.environment,
        release=settings.release,
        traces_sample_rate=settings.sentry_traces_sample_rate,
        send_default_pii=False,
        max_request_body_size="never",
        integrations=integrations,
        before_send=_scrub,
    )

    logger.info(
        "sentry initialized env=%s release=%s", settings.environment, settings.release
    )
