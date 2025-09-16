from __future__ import annotations
"""Simple synchronous in-memory event bus.

Supports subscribe(type, handler) and publish(event). Handlers are invoked in
registration order. This is easily swappable for an async or external broker.
"""
from typing import Callable, Dict, List
from .events import Event
import logging


Handler = Callable[[Event], None]


class EventBus:
    def __init__(self):
        self.subscribers = []

    def subscribe(self, callback):
        self.subscribers.append(callback)

    def publish(self, event):
        for callback in self.subscribers:
            callback(event)


__all__ = ["EventBus"]
