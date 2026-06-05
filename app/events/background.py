"""Defer event side-effects until after the HTTP response is prepared."""

from __future__ import annotations

import logging
from collections.abc import Callable
from contextvars import ContextVar
from typing import Any

logger = logging.getLogger(__name__)

_Handler = Callable[..., None]
_Queue = list[tuple[_Handler, tuple[Any, ...], dict[str, Any]]]
_deferred: ContextVar[_Queue | None] = ContextVar("_deferred_event_handlers", default=None)


def _queue() -> _Queue:
    handlers = _deferred.get()
    if handlers is None:
        handlers = []
        _deferred.set(handlers)
    return handlers


def defer_handler(handler: _Handler, *args: Any, **kwargs: Any) -> None:
    _queue().append((handler, args, kwargs))


def take_deferred_handlers() -> _Queue:
    handlers = _deferred.get()
    _deferred.set(None)
    return handlers or []


def run_handler_safe(handler: _Handler, *args: Any, **kwargs: Any) -> None:
    try:
        handler(*args, **kwargs)
    except Exception:
        logger.exception("Deferred event handler %s failed", handler.__name__)


def flush_deferred_handlers() -> None:
    """Run queued handlers synchronously (for tests and CLI contexts)."""
    for handler, args, kwargs in take_deferred_handlers():
        run_handler_safe(handler, *args, **kwargs)
