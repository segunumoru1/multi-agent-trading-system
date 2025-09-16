from __future__ import annotations
"""Event model definitions used by the in-memory event bus."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict


@dataclass
class Event:
    type: str
    payload: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class MarketDataEvent(Event):
    type: str = "market_data"


@dataclass
class OrderEvent(Event):
    type: str = "order"


@dataclass
class SignalEvent(Event):
    type: str = "signal"


__all__ = ["Event", "MarketDataEvent", "OrderEvent", "SignalEvent"]
