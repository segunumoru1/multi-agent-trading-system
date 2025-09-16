from __future__ import annotations
"""Base agent abstraction.

All concrete agents should inherit from BaseAgent and implement the `step` method.
They receive a shared state dict (graph state) and return a partial update dict
that will be merged into the global state by the orchestrator.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict
import logging


class BaseAgent(ABC):
    name: str = "base"
    role: str = "generic"

    def __init__(self, tools: list[Any] | None = None):
        self.tools = tools or []
        # Each agent gets its own logger named after the concrete class
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    def step(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Perform one reasoning/action step and return state delta."""
        raise NotImplementedError

    def _log(self, message: str):
        """Light wrapper for consistent agent logging."""
        self.logger.info(message)
