"""Simple in-memory rate limiting for sensitive auth endpoints."""

from __future__ import annotations

import time
from collections import defaultdict

from fastapi import Request

_buckets: dict[str, list[float]] = defaultdict(list)

DEFAULT_MAX_ATTEMPTS = 10
DEFAULT_WINDOW_SECONDS = 300


def _client_key(request: Request, scope: str) -> str:
    client = request.client.host if request.client else "unknown"
    return f"{scope}:{client}"


def check_rate_limit(
    request: Request,
    scope: str,
    *,
    max_attempts: int = DEFAULT_MAX_ATTEMPTS,
    window_seconds: int = DEFAULT_WINDOW_SECONDS,
) -> bool:
    """Return True when the client has exceeded the allowed attempt rate."""
    now = time.time()
    key = _client_key(request, scope)
    attempts = [timestamp for timestamp in _buckets[key] if now - timestamp < window_seconds]
    if len(attempts) >= max_attempts:
        _buckets[key] = attempts
        return True
    attempts.append(now)
    _buckets[key] = attempts
    return False
