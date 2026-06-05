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


def run_handler_with_session(handler: _Handler, *args: Any, **kwargs: Any) -> None:
    """Run a handler with its own database session (for post-response execution)."""
    from app.db import db as database
    from app.db import reset_current_session, set_current_session

    session = database.create_session()
    token = set_current_session(session)
    try:
        handler(*args, **kwargs)
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
        reset_current_session(token)


def run_handler_safe(handler: _Handler, *args: Any, **kwargs: Any) -> None:
    try:
        from app.db.session import has_current_session

        if has_current_session():
            handler(*args, **kwargs)
        else:
            run_handler_with_session(handler, *args, **kwargs)
    except Exception:
        logger.exception("Deferred event handler %s failed", handler.__name__)


def flush_deferred_handlers() -> None:
    """Run queued handlers synchronously (for tests and CLI contexts)."""
    for handler, args, kwargs in take_deferred_handlers():
        run_handler_safe(handler, *args, **kwargs)
