"""Rate limiting for sensitive auth endpoints (Redis-backed with in-memory fallback)."""

from __future__ import annotations

import logging
import time
from collections import defaultdict

from fastapi import Request

from app.core.config import get_settings

logger = logging.getLogger(__name__)

_buckets: dict[str, list[float]] = defaultdict(list)
_redis_client = None
_redis_unavailable = False

DEFAULT_MAX_ATTEMPTS = 10
DEFAULT_WINDOW_SECONDS = 300


def _client_key(request: Request, scope: str) -> str:
    client = request.client.host if request.client else "unknown"
    return f"rate_limit:{scope}:{client}"


def _get_redis():
    global _redis_client, _redis_unavailable
    settings = get_settings()
    # Tests always use in-memory buckets so REDIS_URL in .env cannot leak state.
    if settings.is_testing:
        return None
    if _redis_unavailable:
        return None
    if _redis_client is not None:
        return _redis_client

    redis_url = settings.redis_url
    if not redis_url:
        return None

    try:
        import redis

        _redis_client = redis.Redis.from_url(redis_url, decode_responses=True)
        _redis_client.ping()
        return _redis_client
    except Exception as exc:
        logger.warning("Redis rate limiting unavailable, using in-memory fallback: %s", exc)
        _redis_unavailable = True
        return None


def clear_rate_limits() -> None:
    """Reset in-memory buckets and cached Redis client (for tests)."""
    global _redis_client, _redis_unavailable
    _buckets.clear()
    _redis_client = None
    _redis_unavailable = False


def check_rate_limit(
    request: Request,
    scope: str,
    *,
    max_attempts: int = DEFAULT_MAX_ATTEMPTS,
    window_seconds: int = DEFAULT_WINDOW_SECONDS,
) -> bool:
    """Return True when the client has exceeded the allowed attempt rate."""
    key = _client_key(request, scope)
    client = _get_redis()
    if client is not None:
        try:
            count = client.incr(key)
            if count == 1:
                client.expire(key, window_seconds)
            return int(count) > max_attempts
        except Exception as exc:
            logger.warning("Redis rate limit check failed, using in-memory fallback: %s", exc)

    now = time.time()
    attempts = [timestamp for timestamp in _buckets[key] if now - timestamp < window_seconds]
    if len(attempts) >= max_attempts:
        _buckets[key] = attempts
        return True
    attempts.append(now)
    _buckets[key] = attempts
    return False
