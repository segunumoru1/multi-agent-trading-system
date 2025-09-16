from __future__ import annotations
"""Application configuration and settings management.

Uses Pydantic BaseSettings to centralize runtime tunables, allowing values
from environment variables or an optional .env file.
"""
from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic import BaseSettings, Field, validator


class Settings(BaseSettings):
    """Application settings with validation and defaults."""

    # Environment and logging
    env: str = Field("dev", description="Runtime environment name (e.g., dev, prod)")
    log_level: str = Field("INFO", description="Logging level (e.g., DEBUG, INFO, WARNING)")

    # API keys (optional, loaded from env vars)
    openai_api_key: str | None = Field(None, env="OPENAI_API_KEY", description="OpenAI API key")
    tavily_api_key: str | None = Field(None, env="TAVILY_API_KEY", description="Tavily API key")
    finnhub_api_key: str | None = Field(None, env="FINNHUB_API_KEY", description="Finnhub API key")

    # Trading-related settings
    default_symbols: List[str] = Field(
        default_factory=lambda: ["AAPL", "MSFT"],
        description="Default stock symbols to track"
    )
    risk_max_position_pct: float = Field(
        0.15,
        ge=0.0,
        le=1.0,
        description="Maximum position percentage of portfolio (0.0 to 1.0)"
    )

    # Storage
    vector_db_dir: Path = Field(
        Path(".chromadb"),
        description="Directory for local Chroma vector database storage"
    )

    class Config:
        env_file = ".env"
        case_sensitive = False

    @validator("default_symbols", pre=True)
    @classmethod
    def _parse_symbols(cls, v: str | List[str]) -> List[str]:
        """Parse default_symbols from a comma-separated string or list."""
        if isinstance(v, str):
            return [s.strip() for s in v.split(",") if s.strip()]
        return v

    @validator("vector_db_dir")
    @classmethod
    def _ensure_dir(cls, v: Path) -> Path:
        """Ensure the vector database directory exists."""
        v.mkdir(parents=True, exist_ok=True)
        return v


@lru_cache
def get_settings() -> Settings:
    """Get cached application settings instance."""
    return Settings()


# Global settings instance
settings = get_settings()
