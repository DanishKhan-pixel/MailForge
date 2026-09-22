"""Simple in-memory rate limiting dependency."""

from __future__ import annotations

import time
from collections import defaultdict, deque
from collections.abc import Callable
from threading import Lock

from fastapi import HTTPException, Request, Response, status

_requests: dict[str, deque[float]] = defaultdict(deque)
_lock = Lock()

MAX_RATE_LIMIT_BUCKETS = 10_000


def _sweep_expired_buckets(now: float) -> None:
    """Prune expired request timestamps and drop buckets that became empty."""
    for key, queue in list(_requests.items()):
        window_seconds = int(key.rsplit(":", 1)[-1])
        while queue and now - queue[0] > window_seconds:
            queue.popleft()
        if not queue:
            del _requests[key]


def _evict_oldest_buckets() -> None:
    """Evict least recently active buckets when capacity is exceeded."""
    over = len(_requests) - MAX_RATE_LIMIT_BUCKETS
    if over <= 0:
        return
    ordered = sorted(
        ((key, queue[-1]) for key, queue in _requests.items() if queue),
        key=lambda pair: pair[1],
    )
    for key, _ in ordered[:over]:
        del _requests[key]
        if len(_requests) <= MAX_RATE_LIMIT_BUCKETS:
            return


def rate_limit(max_requests: int, window_seconds: int) -> Callable[[Request, Response], None]:
    """Factory creating a FastAPI dependency for client IP rate limiting.

    Each unique (limit, window) configuration gets its own independent bucket so
    different endpoints do not share or exhaust each other's allowance. Bucket
    storage is bounded: when the number of tracked buckets exceeds the cap, stale
    empty buckets are swept and the least recently active buckets are evicted to
    keep memory usage bounded.

    When FastAPI supplies a Response object, standard ``X-RateLimit-*`` headers
    are attached so clients can observe remaining quota and reset timing.

    Args:
        max_requests: Maximum allowed requests within the sliding window.
        window_seconds: Time window duration in seconds.

    Returns:
        FastAPI dependency function validating rate limit status.

    Raises:
        HTTPException: 429 TOO MANY REQUESTS if limit is exceeded.
    """

    def dependency(request: Request, response: Response) -> None:
        ip = request.client.host if request.client else "unknown"
        key = f"{ip}:{max_requests}:{window_seconds}"
        now = time.time()
        with _lock:
            queue = _requests[key]
            while queue and now - queue[0] > window_seconds:
                queue.popleft()
            if len(queue) >= max_requests:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit exceeded. Please retry later.",
                )
            queue.append(now)
            if len(_requests) > MAX_RATE_LIMIT_BUCKETS:
                _sweep_expired_buckets(now)
                _evict_oldest_buckets()

        elapsed = now - queue[0] if queue else 0
        response.headers["X-RateLimit-Limit"] = str(max_requests)
        response.headers["X-RateLimit-Remaining"] = str(max(max_requests - len(queue), 0))
        response.headers["X-RateLimit-Reset"] = str(int(max(window_seconds - elapsed, 0)))

    return dependency


def reset_rate_limits() -> None:
    """Clear all stored request history from memory. Useful for testing."""
    with _lock:
        _requests.clear()


