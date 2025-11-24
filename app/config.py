from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    """Runtime configuration shared across FastAPI and Streamlit."""

    app_name: str = Field("Support Triage Agent", env="APP_NAME")
    environment: str = Field("development", env="ENVIRONMENT")
    kb_path: Path = Field(Path("kb") / "kb.json", env="KB_PATH")
    kb_similarity_threshold: float = Field(0.35, env="KB_SIMILARITY_THRESHOLD")
    max_related_results: int = Field(3, env="MAX_RELATED_RESULTS")
    llm_provider: str = Field("mock", env="LLM_PROVIDER")
    groq_api_key: Optional[str] = Field(None, env="GROQ_API_KEY")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()
