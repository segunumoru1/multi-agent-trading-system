from __future__ import annotations
"""Lightweight tracing utilities.

Currently provides:
  * span(name): context manager logging start/end + duration (ms)
  * init_langsmith(): idempotent enabler for LangSmith tracing if API key present
  * tracing_enabled(): convenience predicate (LangSmith or explicit flag)
"""
import time
import logging
import os
from contextlib import contextmanager
from typing import Optional

logger = logging.getLogger("tracing")
_LANGSMITH_INITIALIZED = False


@contextmanager
def span(name: str):
        """Measure a named code block.

        Usage:
                with span("research_node"):
                        ...
        """
        start = time.time()
        logger.debug("Span start: %s", name)
        try:
                yield
        finally:
                dur = (time.time() - start) * 1000
                logger.debug("Span end: %s duration_ms=%.2f", name, dur)


def init_langsmith(project: Optional[str] = None) -> bool:
        """Initialize LangSmith tracing if proper environment variables are present.

        Required:
          LANGCHAIN_API_KEY
        Optional / defaulted:
          LANGCHAIN_TRACING_V2 (defaults to 'true')
          LANGCHAIN_PROJECT (can be overridden via param)

        Returns True if initialized, False if configuration absent. Safe to call multiple times.
        """
        global _LANGSMITH_INITIALIZED
        if _LANGSMITH_INITIALIZED:
                return True
        api_key = os.getenv("LANGCHAIN_API_KEY")
        if not api_key:
                logger.debug("LangSmith not initialized: LANGCHAIN_API_KEY missing")
                return False
        os.environ.setdefault("LANGCHAIN_TRACING_V2", "true")
        if project:
                os.environ["LANGCHAIN_PROJECT"] = project
        _LANGSMITH_INITIALIZED = True
        logger.info("LangSmith tracing enabled project=%s", os.getenv("LANGCHAIN_PROJECT", "default"))
        return True


def tracing_enabled() -> bool:
        """Return True if any tracing mechanism should be active.

        Conditions:
          * LangSmith initialized (API key present) OR
          * Explicit feature flag: TRACING=1 in environment.
        """
        if _LANGSMITH_INITIALIZED:
                return True
        if os.getenv("TRACING") == "1":
                return True
        # Also treat presence of API key (without explicit init yet) as intent.
        if os.getenv("LANGCHAIN_API_KEY"):
                return True
        return False


__all__ = ["span", "init_langsmith", "tracing_enabled"]
