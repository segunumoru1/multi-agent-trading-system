"""Database-specific configuration settings."""

from sqlalchemy.engine.url import URL
from .config import settings


def get_database_url() -> str:
    """Generate database URL from settings."""
    return str(URL.create(
        drivername="postgresql",
        username=settings.db_username,
        password=settings.db_password,
        host=settings.db_host,
        port=settings.db_port,
        database=settings.db_name
    ))


def get_redis_url() -> str:
    """Generate Redis URL from settings."""
    return f"redis://{settings.redis_host}:{settings.redis_port}/0"