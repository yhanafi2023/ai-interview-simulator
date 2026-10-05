from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    environment: str = "development"
    database_url: str = "postgresql+psycopg://interview:interview@localhost:5432/interview"
    redis_url: str = "redis://localhost:6379/0"
    cors_origins: list[str] = ["http://localhost:5173"]
    jwt_secret: str = "dev-only-secret-change-in-production"
    access_token_minutes: int = 15
    refresh_token_days: int = 7
    cookie_secure: bool = False
    cookie_samesite: str = "lax"
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-5-20250929"
    anthropic_max_tokens: int = 1024
    anthropic_timeout_seconds: float = 30.0
    anthropic_max_retries: int = 3

    llm_daily_call_budget: int = 200
    llm_user_daily_call_budget: int = 20
    grading_bucket_capacity: int = 20
    grading_bucket_refill_per_day: int = 20
    login_bucket_capacity: int = 10
    login_bucket_refill_per_hour: int = 10


settings = Settings()
