import os
from typing import Optional

def get_secret(key: str, default: Optional[str] = None) -> str:
    """Get a secret from environment variables."""
    value = os.getenv(key, default)
    if value is None:
        raise ValueError(f"Secret '{key}' not found in environment variables")
    return value