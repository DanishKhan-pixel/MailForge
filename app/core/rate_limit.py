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
    """Rate limit requests by client IP in memory."""

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
