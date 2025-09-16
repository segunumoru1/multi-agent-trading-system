from __future__ import annotations
"""Application configuration and settings management.

Uses Pydantic BaseSettings to centralize runtime tunables, allowing values
from environment variables or an optional .env file.
"""
from functools import lru_cache
from pathlib import Path
from typing import List, Optional

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

    # Database Configuration (PostgreSQL)
    db_host: str = Field("localhost", env="DB_HOST", description="Database host")
    db_port: str = Field("5432", env="DB_PORT", description="Database port")
    db_name: str = Field("financial_agents", env="DB_NAME", description="Database name")
    db_username: str = Field("postgres", env="DB_USERNAME", description="Database username")
    db_password: str | None = Field(None, env="DB_PASSWORD", description="Database password")

    # LLM Configuration
    deep_think_llm: str = Field("gpt-4", description="LLM model for deep thinking tasks")
    quick_think_llm: str = Field("gpt-3.5-turbo", description="LLM model for quick tasks")
    backend_url: str = Field("https://api.openai.com/v1", env="BACKEND_URL", description="LLM API backend URL")

    # Trading-related settings
    default_symbols: List[str] = Field(
        default_factory=lambda: ["AAPL", "MSFT", "NVDA"],
        description="Default stock symbols to track"
    )
    risk_max_position_pct: float = Field(
        0.15,
        ge=0.0,
        le=1.0,
        description="Maximum position percentage of portfolio (0.0 to 1.0)"
    )
    risk_tolerance: float = Field(
        0.02,
        ge=0.0,
        le=0.1,
        description="Risk tolerance per trade (0.0 to 0.1)"
    )

    # Service Configuration
    enable_backtesting: bool = Field(True, description="Enable backtesting functionality")
    enable_streaming: bool = Field(False, description="Enable real-time data streaming")
    enable_portfolio_tracking: bool = Field(True, description="Enable portfolio tracking")

    # Caching and Performance
    redis_host: str = Field("localhost", env="REDIS_HOST", description="Redis cache host")
    redis_port: int = Field(6379, env="REDIS_PORT", description="Redis cache port")
    cache_ttl: int = Field(3600, description="Cache TTL in seconds")

    # Monitoring
    enable_prometheus: bool = Field(True, description="Enable Prometheus metrics")
    prometheus_port: int = Field(8001, description="Prometheus metrics port")

    # Data streaming configuration
    data_source: str = Field("yahoo", description="Data source: yahoo, polygon, or mock")
    yahoo_poll_interval: int = Field(60, description="Yahoo Finance polling interval in seconds")
    polygon_api_key: str | None = Field(None, env="POLYGON_API_KEY", description="Polygon.io API key")

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

    @validator("db_password")
    @classmethod
    def _validate_db_password(cls, v: Optional[str]) -> Optional[str]:
        """Ensure database password is provided in production."""
        if cls().env == "prod" and not v:
            raise ValueError("Database password is required in production environment")
        return v


@lru_cache
def get_settings() -> Settings:
    """Get cached application settings instance."""
    return Settings()


# Global settings instance
settings = get_settings()