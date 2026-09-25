"""ASGI middleware for structured HTTP request logging and tracing."""

from __future__ import annotations

import logging
import time
import uuid

logger = logging.getLogger(__name__)

REQUEST_ID_HEADER = "x-request-id"


class RequestIdMiddleware:
    """Generate or forward a request identifier and echo it on the response."""

    def __init__(self, app) -> None:
        self.app = app

    async def __call__(self, scope, receive, send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request_id = None
        for name, value in scope.get("headers", []):
            if name.lower() == REQUEST_ID_HEADER.encode():
                request_id = value.decode("latin-1")
                break
        if not request_id:
            request_id = uuid.uuid4().hex
        scope.setdefault("state", {})["request_id"] = request_id

        async def _send_with_request_id(message) -> None:
            if message["type"] == "http.response.start":
                message.setdefault("headers", [])
                message["headers"].append((REQUEST_ID_HEADER.encode(), request_id.encode("latin-1")))
            await send(message)

        await self.app(scope, receive, _send_with_request_id)


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
        request_id = scope.get("state", {}).get("request_id", "-")

        async def _send_with_status(message) -> None:
            if message["type"] == "http.response.start":
                status_code["value"] = message["status"]
            await send(message)

        try:
            await self.app(scope, receive, _send_with_status)
        finally:
            duration_ms = (time.perf_counter() - start) * 1000
            logger.info(
                "%s %s -> %s in %.1fms rid=%s",
                scope["method"],
                scope["path"],
                status_code["value"],
                duration_ms,
                request_id,
            )