from functools import lru_cache
from pathlib import Path
from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    app_name: str = Field(default="Support Triage Agent")
    environment: str = Field(default="development")
    kb_path: Path = Field(default=Path("kb") / "kb.json")
    similarity_threshold: float = Field(default=0.35)
    max_related_results: int = Field(default=3)

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()
