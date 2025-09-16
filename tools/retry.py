from __future__ import annotations
"""Simple retry decorator with exponential backoff."""
import time
import functools
import logging
from typing import Callable, Type, Tuple


def retry(
    exceptions: Tuple[Type[BaseException], ...] = (Exception,),
    tries: int = 3,
    delay: float = 0.5,
    backoff: float = 2.0,
    logger: logging.Logger | None = None,
):
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            _tries, _delay = tries, delay
            while _tries > 0:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:  # type: ignore[misc]
                    _tries -= 1
                    if _tries == 0:
                        raise
                    log = logger or logging.getLogger(func.__name__)
                    log.debug("Retrying %s after error: %s (remaining=%d)", func.__name__, e, _tries)
                    time.sleep(_delay)
                    _delay *= backoff
        return wrapper
    return decorator

__all__ = ["retry"]
