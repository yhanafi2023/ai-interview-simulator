from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import auth, health, questions
from app.api import health
from app.config import settings

app = FastAPI(
    title="AI Interview Simulator API",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(questions.router)