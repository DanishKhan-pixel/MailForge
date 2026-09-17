"""Unit tests for common Pydantic response and query schemas."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.schemas.common import HealthResponse, MessageResponse, PaginationParams


def test_message_response_schema() -> None:
    resp = MessageResponse(message="Operation successful")
    assert resp.message == "Operation successful"


def test_health_response_schema() -> None:
    health = HealthResponse()
    assert health.status == "ok"
    custom_health = HealthResponse(status="degraded")
    assert custom_health.status == "degraded"


def test_error_detail_schema() -> None:
    from app.schemas.common import ErrorDetail

    err = ErrorDetail(detail="Invalid recipient format")
    assert err.detail == "Invalid recipient format"
    assert err.code is None

    err_with_code = ErrorDetail(detail="Quota exceeded", code="RATE_LIMIT_EXCEEDED")
    assert err_with_code.detail == "Quota exceeded"
    assert err_with_code.code == "RATE_LIMIT_EXCEEDED"



def test_pagination_params_defaults() -> None:
    params = PaginationParams()
    assert params.page == 1
    assert params.page_size == 10


def test_pagination_params_custom() -> None:
    params = PaginationParams(page=3, page_size=50)
    assert params.page == 3
    assert params.page_size == 50


def test_pagination_params_validation_error() -> None:
    with pytest.raises(ValidationError):
        PaginationParams(page=0)

    with pytest.raises(ValidationError):
        PaginationParams(page_size=200)
