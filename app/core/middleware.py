"""ASGI middleware for structured HTTP request logging."""

from __future__ import annotations

import logging
import time

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware:
    """Log HTTP method, path, status code, and duration for every request."""

    def __init__(self, app) -> None:
        self.app = app

    async def __call__(self, scope, receive, send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        start = time.perf_counter()
        status_code = {"value": 500}

        async def _send_with_status(message) -> None:
            if message["type"] == "http.response.start":
                status_code["value"] = message["status"]
            await send(message)

        try:
            await self.app(scope, receive, _send_with_status)
        finally:
            duration_ms = (time.perf_counter() - start) * 1000
            logger.info(
                "%s %s -> %s in %.1fms",
                scope["method"],
                scope["path"],
                status_code["value"],
                duration_ms,
            )