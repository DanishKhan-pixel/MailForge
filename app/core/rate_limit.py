"""Simple in-memory rate limiting dependency."""

from __future__ import annotations

import time
from collections import defaultdict, deque
from collections.abc import Callable
from threading import Lock

from fastapi import HTTPException, Request, status

_requests: dict[str, deque[float]] = defaultdict(deque)
_lock = Lock()


def rate_limit(max_requests: int, window_seconds: int) -> Callable[[Request], None]:
    """Factory creating a FastAPI dependency for client IP rate limiting.

    Args:
        max_requests: Maximum allowed requests within the sliding window.
        window_seconds: Time window duration in seconds.

    Returns:
        FastAPI dependency function validating rate limit status.

    Raises:
        HTTPException: 429 TOO MANY REQUESTS if limit is exceeded.
    """

    def dependency(request: Request) -> None:
        key = request.client.host if request.client else "unknown"
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

    return dependency


def reset_rate_limits() -> None:
    """Clear all stored request history from memory. Useful for testing."""
    with _lock:
        _requests.clear()


