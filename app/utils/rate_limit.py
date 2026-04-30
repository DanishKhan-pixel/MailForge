"""Simple in-memory rate limiting dependency for FastAPI routes."""

from __future__ import annotations

import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request, status

# Per-endpoint request history by client IP.
_REQUEST_LOG: dict[str, deque[float]] = defaultdict(deque)


def rate_limit(max_requests: int = 10, window_seconds: int = 60):
    """Factory that returns a FastAPI dependency enforcing request limits."""

    async def limiter(request: Request) -> None:
        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
        window_start = now - window_seconds
        logs = _REQUEST_LOG[client_ip]

        while logs and logs[0] < window_start:
            logs.popleft()

        if len(logs) >= max_requests:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please retry later.",
            )

        logs.append(now)

    return limiter
