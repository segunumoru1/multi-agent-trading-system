from __future__ import annotations
"""State models for the trading LangGraph.

This defines the canonical shape of the evolving conversation / decision state.
"""
from typing import List, Any, Dict
from pydantic import BaseModel, Field


class TradingState(BaseModel):
    research_insights: List[str] = Field(default_factory=list)
    signals: List[Dict[str, Any]] = Field(default_factory=list)
    risk_evaluated_signals: List[Dict[str, Any]] = Field(default_factory=list)
    orders: List[Dict[str, Any]] = Field(default_factory=list)
    done: bool = False

    def merge(self, delta: Dict[str, Any]):
        """Merge a partial delta into the state (simple strategy)."""
        for k, v in delta.items():
            setattr(self, k, v)
        return self
