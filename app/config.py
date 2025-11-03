"""Configuration settings for the application."""
import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/football_db")

    # ML Model
    ML_MODEL_VERSION: str = os.getenv("ML_MODEL_VERSION", "v1.0")
    PERF_THRESHOLD_LOW: float = 45.0
    PERF_THRESHOLD_HIGH: float = 75.0

    # API
    API_VERSION: str = "v1"
    DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    model_config = {
        "extra": "ignore",  # Ignora variabili extra da .env
        "env_file": ".env",
        "case_sensitive": True
    }


settings = Settings()
