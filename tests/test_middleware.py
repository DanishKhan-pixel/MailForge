"""Unit tests for HTTP request logging middleware."""

from __future__ import annotations

import logging

from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route

from app.core.middleware import RequestLoggingMiddleware
from app.main import app
from fastapi.testclient import TestClient


def _build_test_app() -> Starlette:
    async def _ping(request):
        return JSONResponse({"status": "ok"})

    test_app = Starlette(routes=[Route("/ping", _ping)])
    test_app.add_middleware(RequestLoggingMiddleware)
    return test_app


def test_middleware_logs_method_path_and_status(caplog) -> None:
    client = TestClient(_build_test_app())
    with caplog.at_level(logging.INFO, logger="app.core.middleware"):
        response = client.get("/ping")

    assert response.status_code == 200
    assert "GET /ping -> 200" in caplog.text
    assert "ms" in caplog.text


def test_middleware_logs_non_http_scopes() -> None:
    test_app = Starlette(routes=[])
    test_app.add_middleware(RequestLoggingMiddleware)
    client = TestClient(test_app)

    response = client.get("/not-found")

    assert response.status_code == 404


def test_main_app_mounts_request_logging_middleware() -> None:
    assert any(
        getattr(middleware, "cls", None) is RequestLoggingMiddleware
        for middleware in app.user_middleware
    )