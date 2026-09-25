"""Unit tests for HTTP request logging and request-id middleware."""

from __future__ import annotations

import logging

from fastapi.testclient import TestClient
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route

from app.core.middleware import RequestIdMiddleware, RequestLoggingMiddleware
from app.main import app


def _build_test_app() -> Starlette:
    async def _ping(request):
        return JSONResponse({"status": "ok"})

    test_app = Starlette(routes=[Route("/ping", _ping)])
    test_app.add_middleware(RequestLoggingMiddleware)
    test_app.add_middleware(RequestIdMiddleware)
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


def test_request_id_generated_and_returned() -> None:
    client = TestClient(_build_test_app())
    response = client.get("/ping")

    request_id = response.headers["X-Request-Id"]
    assert request_id
    assert len(request_id) == 32


def test_request_id_preserves_provided_header() -> None:
    client = TestClient(_build_test_app())
    response = client.get("/ping", headers={"X-Request-Id": "provided-rid-42"})

    assert response.headers["X-Request-Id"] == "provided-rid-42"


def test_log_line_includes_request_id(caplog) -> None:
    client = TestClient(_build_test_app())
    with caplog.at_level(logging.INFO, logger="app.core.middleware"):
        client.get("/ping", headers={"X-Request-Id": "rid-42"})

    assert "rid=rid-42" in caplog.text


def test_main_app_mounts_request_id_middleware() -> None:
    assert any(
        getattr(middleware, "cls", None) is RequestIdMiddleware for middleware in app.user_middleware
    )