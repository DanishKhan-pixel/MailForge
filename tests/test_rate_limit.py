"""Unit tests for in-memory rate limiting dependency."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException, Request, Response

from app.core.rate_limit import rate_limit, reset_rate_limits


@pytest.fixture(autouse=True)
def _clear_limits() -> None:
    reset_rate_limits()


def test_rate_limit_allows_under_threshold() -> None:
    limiter = rate_limit(max_requests=3, window_seconds=60)
    request = MagicMock(spec=Request)
    request.client.host = "192.168.1.1"

    # 3 requests should succeed without error
    limiter(request, Response())
    limiter(request, Response())
    limiter(request, Response())


def test_rate_limit_exceeds_threshold() -> None:
    limiter = rate_limit(max_requests=2, window_seconds=60)
    request = MagicMock(spec=Request)
    request.client.host = "192.168.1.2"

    limiter(request, Response())
    limiter(request, Response())

    with pytest.raises(HTTPException) as exc_info:
        limiter(request, Response())

    assert exc_info.value.status_code == 429
    assert "Rate limit exceeded" in exc_info.value.detail


def test_reset_rate_limits_clears_counter() -> None:
    limiter = rate_limit(max_requests=1, window_seconds=60)
    request = MagicMock(spec=Request)
    request.client.host = "192.168.1.3"

    limiter(request, Response())
    reset_rate_limits()

    # After reset, a request should be allowed again
    limiter(request, Response())


def test_rate_limit_buckets_isolated_across_configurations() -> None:
    strict_limiter = rate_limit(max_requests=1, window_seconds=60)
    generous_limiter = rate_limit(max_requests=3, window_seconds=60)
    request = MagicMock(spec=Request)
    request.client.host = "192.168.1.4"

    strict_limiter(request, Response())
    # Exhausting the strict limiter must not affect the generous one
    with pytest.raises(HTTPException) as exc_info:
        strict_limiter(request, Response())
    assert exc_info.value.status_code == 429

    generous_limiter(request, Response())
    generous_limiter(request, Response())
    generous_limiter(request, Response())


def test_rate_limit_buckets_isolated_from_other_ip() -> None:
    limiter = rate_limit(max_requests=1, window_seconds=60)
    first = MagicMock(spec=Request)
    first.client.host = "192.168.1.5"
    second = MagicMock(spec=Request)
    second.client.host = "192.168.1.6"

    limiter(first, Response())
    with pytest.raises(HTTPException):
        limiter(first, Response())

    # A different client IP retains its own independent allowance
    limiter(second, Response())


def test_rate_limit_evicts_oldest_buckets_over_capacity(monkeypatch) -> None:
    import importlib

    rate_limit_module = importlib.import_module("app.core.rate_limit")

    monkeypatch.setattr(rate_limit_module, "MAX_RATE_LIMIT_BUCKETS", 5)
    limiter = rate_limit(max_requests=1, window_seconds=60)

    for i in range(20):
        request = MagicMock(spec=Request)
        request.client.host = f"10.0.0.{i}"
        limiter(request, Response())

    assert len(rate_limit_module._requests) <= 5
    # The oldest active bucket should have been evicted
    assert "10.0.0.0:1:60" not in rate_limit_module._requests


def test_rate_limit_sweeps_expired_buckets_on_overflow(monkeypatch) -> None:
    import importlib

    rate_limit_module = importlib.import_module("app.core.rate_limit")

    monkeypatch.setattr(rate_limit_module, "MAX_RATE_LIMIT_BUCKETS", 4)
    limiter = rate_limit(max_requests=1, window_seconds=60)

    for i in range(5):
        request = MagicMock(spec=Request)
        request.client.host = f"172.16.0.{i}"
        limiter(request, Response())

    assert len(rate_limit_module._requests) <= 4


def test_rate_limit_attaches_quota_headers() -> None:
    limiter = rate_limit(max_requests=3, window_seconds=60)
    request = MagicMock(spec=Request)
    request.client.host = "10.1.0.1"
    response = Response()

    limiter(request, response)

    assert response.headers["X-RateLimit-Limit"] == "3"
    assert response.headers["X-RateLimit-Remaining"] == "2"
    assert int(response.headers["X-RateLimit-Reset"]) <= 60


def test_rate_limit_reports_zero_remaining_at_capacity() -> None:
    limiter = rate_limit(max_requests=2, window_seconds=30)
    request = MagicMock(spec=Request)
    request.client.host = "10.1.0.2"

    response = Response()
    limiter(request, response)
    response = Response()
    limiter(request, response)

    assert response.headers["X-RateLimit-Limit"] == "2"
    assert response.headers["X-RateLimit-Remaining"] == "0"

    with pytest.raises(HTTPException):
        limiter(request, Response())
