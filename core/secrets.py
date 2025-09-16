from __future__ import annotations
"""Secrets abstraction with masking and validation."""
import os
from typing import Optional, Dict

SENSITIVE_KEYS = {"OPENAI_API_KEY", "TAVILY_API_KEY", "FINNHUB_API_KEY"}


def get_secret(name: str) -> Optional[str]:
    return os.environ.get(name)


def mask_secret(value: Optional[str]) -> str:
    if not value:
        return "<missing>"
    if len(value) <= 6:
        return "***"
    return value[:3] + "***" + value[-3:]


def snapshot_secrets() -> Dict[str, str]:
    return {k: mask_secret(os.environ.get(k)) for k in SENSITIVE_KEYS}


__all__ = ["get_secret", "mask_secret", "snapshot_secrets"]
