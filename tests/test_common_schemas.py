"""Unit tests for common Pydantic response and query schemas."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.schemas.common import MessageResponse, PaginationParams


def test_message_response_schema() -> None:
    resp = MessageResponse(message="Operation successful")
    assert resp.message == "Operation successful"


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
