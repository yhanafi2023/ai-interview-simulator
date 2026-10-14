import logging
import uuid

import sentry_sdk
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth, health, jobs, metrics, questions, sessions
from app.config import settings
from app.observability import init_sentry, request_id_var

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s | %(message)s",
)

init_sentry()

app = FastAPI(
    title="AI Interview Simulator API",
    version="0.1.0",
)


@app.middleware("http")
async def request_id_middleware(request: Request, call_next):  # noqa: ANN001, ANN201
    request_id = request.headers.get("x-request-id") or uuid.uuid4().hex
    request_id_var.set(request_id)
    sentry_sdk.set_tag("request_id", request_id)
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(questions.router)
app.include_router(sessions.router)
app.include_router(jobs.router)
app.include_router(metrics.router)
