from __future__ import annotations
"""Graph callback / instrumentation helpers.

This module provides a light abstraction so each graph node can be wrapped
with a timing span and (optionally) future LangChain / LangSmith callbacks.

Design goals:
  * Zero-op overhead if tracing disabled.
  * Minimal dependency surface (avoid importing heavy libs if unneeded).
  * Easy extension: add on_node_error / on_node_result hooks later.
"""
from typing import Callable, Dict, Any, TYPE_CHECKING
import logging
from core.tracing import span, tracing_enabled

logger = logging.getLogger("graph.callbacks")


if TYPE_CHECKING:  # import only for type checking to avoid circular
    from .trading_graph import GraphState  # noqa: F401


class NodeCallbackManager:
    def __init__(self, enabled: bool | None = None):
        self.enabled = tracing_enabled() if enabled is None else enabled

    def wrap(self, name: str, fn: Callable[[Any], Dict[str, Any]]):  # type: ignore[override]
        """Return a wrapped function that instruments execution.

        If tracing disabled returns original function (micro overhead only).
        """
        if not self.enabled:
            return fn  # type: ignore[return-value]

        def _wrapped(state: Dict[str, Any]) -> Dict[str, Any]:  # keep Dict[str, Any] to stay generic
            with span(f"node.{name}"):
                try:
                    result = fn(state)
                    logger.debug("Node %s produced keys=%s", name, list(result.keys()))
                    return result
                except Exception as e:
                    logger.exception("Node %s error: %s", name, e)
                    raise
    return _wrapped  # type: ignore[return-value]


__all__ = ["NodeCallbackManager"]