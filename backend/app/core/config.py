import warnings
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "AI Workflow Automation System"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    DATABASE_URL: str = "sqlite:///./data/agent.db"

    LLM_API_KEY: Optional[str] = None
    AI_MODEL: str = ""
    AI_MODE: str = "auto"

    CONFIDENCE_AUTO_THRESHOLD: float = 78.0
    CONFIDENCE_REVIEW_THRESHOLD: float = 50.0

    HIGH_VALUE_THRESHOLD: float = 10000.0

    SECRET_KEY: str = ""

    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ]

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)


settings = Settings()

if settings.SECRET_KEY == "":
    warnings.warn(
        "SECRET_KEY is the insecure development default. "
        "Set SECRET_KEY in your .env for any non-local environment.",
        stacklevel=2,
    )
