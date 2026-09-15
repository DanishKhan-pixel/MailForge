"""Unit tests for in-memory rate limiting dependency."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException, Request

from app.core.rate_limit import rate_limit, reset_rate_limits


@pytest.fixture(autouse=True)
def _clear_limits() -> None:
    reset_rate_limits()


def test_rate_limit_allows_under_threshold() -> None:
    limiter = rate_limit(max_requests=3, window_seconds=60)
    request = MagicMock(spec=Request)
    request.client.host = "192.168.1.1"

    # 3 requests should succeed without error
    limiter(request)
    limiter(request)
    limiter(request)


def test_rate_limit_exceeds_threshold() -> None:
    limiter = rate_limit(max_requests=2, window_seconds=60)
    request = MagicMock(spec=Request)
    request.client.host = "192.168.1.2"

    limiter(request)
    limiter(request)

    with pytest.raises(HTTPException) as exc_info:
        limiter(request)

    assert exc_info.value.status_code == 429
    assert "Rate limit exceeded" in exc_info.value.detail


def test_reset_rate_limits_clears_counter() -> None:
    limiter = rate_limit(max_requests=1, window_seconds=60)
    request = MagicMock(spec=Request)
    request.client.host = "192.168.1.3"

    limiter(request)
    reset_rate_limits()

    # After reset, a request should be allowed again
    limiter(request)


def test_rate_limit_buckets_isolated_across_configurations() -> None:
    strict_limiter = rate_limit(max_requests=1, window_seconds=60)
    generous_limiter = rate_limit(max_requests=3, window_seconds=60)
    request = MagicMock(spec=Request)
    request.client.host = "192.168.1.4"

    strict_limiter(request)
    # Exhausting the strict limiter must not affect the generous one
    with pytest.raises(HTTPException) as exc_info:
        strict_limiter(request)
    assert exc_info.value.status_code == 429

    generous_limiter(request)
    generous_limiter(request)
    generous_limiter(request)


def test_rate_limit_buckets_isolated_from_other_ip() -> None:
    limiter = rate_limit(max_requests=1, window_seconds=60)
    first = MagicMock(spec=Request)
    first.client.host = "192.168.1.5"
    second = MagicMock(spec=Request)
    second.client.host = "192.168.1.6"

    limiter(first)
    with pytest.raises(HTTPException):
        limiter(first)

    # A different client IP retains its own independent allowance
    limiter(second)
