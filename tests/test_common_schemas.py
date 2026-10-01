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


def test_api_status_response_schema() -> None:
    from app.schemas.common import ApiStatusResponse

    status_resp = ApiStatusResponse(app_name="MailForge", version="2.0.0", environment="production")
    assert status_resp.app_name == "MailForge"
    assert status_resp.version == "2.0.0"
    assert status_resp.environment == "production"


def test_system_info_response_schema() -> None:
    from app.schemas.common import SystemInfoResponse

    sys_info = SystemInfoResponse(
        app_name="MailForge",
        version="2.0.0",
        environment="development",
        debug=True,
        testing=False,
    )
    assert sys_info.app_name == "MailForge"
    assert sys_info.debug is True
    assert sys_info.testing is False


def test_bulk_delete_response_schema() -> None:
    from app.schemas.common import BulkDeleteResponse

    res = BulkDeleteResponse(deleted_count=12)
    assert res.deleted_count == 12
    assert "deleted successfully" in res.message

    with pytest.raises(ValidationError):
        BulkDeleteResponse(deleted_count=-1)


def test_batch_operation_result_schema() -> None:
    from app.schemas.common import BatchOperationResult

    batch = BatchOperationResult(total_processed=100, success_count=98, failure_count=2)
    assert batch.total_processed == 100
    assert batch.success_count == 98
    assert batch.failure_count == 2

    with pytest.raises(ValidationError):
        BatchOperationResult(total_processed=-1, success_count=0)


def test_filter_params_schema() -> None:
    from app.schemas.common import FilterParams

    filters = FilterParams(status="sent", search="alice")
    assert filters.status == "sent"
    assert filters.search == "alice"

    empty_filters = FilterParams()
    assert empty_filters.status is None
    assert empty_filters.search is None


def test_date_range_filter_schema() -> None:
    from datetime import datetime, timezone
    from app.schemas.common import DateRangeFilter

    now = datetime.now(timezone.utc)
    dr = DateRangeFilter(start_date=now, end_date=now)
    assert dr.start_date == now
    assert dr.end_date == now

    empty_dr = DateRangeFilter()
    assert empty_dr.start_date is None
    assert empty_dr.end_date is None


def test_sort_params_schema() -> None:
    from app.schemas.common import SortParams

    sp = SortParams()
    assert sp.sort_by == "created_at"
    assert sp.order == "desc"

    custom_sp = SortParams(sort_by="name", order="asc")
    assert custom_sp.sort_by == "name"
    assert custom_sp.order == "asc"

    with pytest.raises(ValidationError):
        SortParams(order="invalid")



def test_pagination_params_defaults() -> None:
    params = PaginationParams()
    assert params.page == 1
    assert params.page_size == 10


def test_pagination_params_custom() -> None:
    params = PaginationParams(page=3, page_size=50)
    assert params.page == 3
    assert params.page_size == 50


def test_pagination_params_offset() -> None:
    p1 = PaginationParams(page=1, page_size=10)
    assert p1.offset == 0

    p3 = PaginationParams(page=3, page_size=20)
    assert p3.offset == 40


def test_pagination_params_validation_error() -> None:
    with pytest.raises(ValidationError):
        PaginationParams(page=0)

    with pytest.raises(ValidationError):
        PaginationParams(page_size=200)
