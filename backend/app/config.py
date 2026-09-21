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
    cookie_secure : bool = False
    cookie_samesite : str = "lax"

settings = Settings()