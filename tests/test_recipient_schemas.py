"""Unit tests for recipient Pydantic schemas."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.schemas.recipient import RecipientItem, RecipientListResponse, SendOptions, UploadResponse


def test_recipient_item_valid() -> None:
    item = RecipientItem(email="user@example.com", name="User Name")
    assert item.email == "user@example.com"
    assert item.name == "User Name"


def test_recipient_item_optional_name() -> None:
    item = RecipientItem(email="user@example.com")
    assert item.email == "user@example.com"
    assert item.name is None


def test_recipient_item_rejects_invalid_email() -> None:
    with pytest.raises(ValidationError):
        RecipientItem(email="invalid-email", name="User")


def test_recipient_item_rejects_overlong_name() -> None:
    with pytest.raises(ValidationError):
        RecipientItem(email="user@example.com", name="x" * 201)


def test_recipient_item_accepts_max_length_name() -> None:
    item = RecipientItem(email="user@example.com", name="x" * 200)
    assert len(item.name or "") == 200


def test_recipient_detail_rejects_overlong_name() -> None:
    from app.schemas.recipient import RecipientDetail

    with pytest.raises(ValidationError):
        RecipientDetail(id=1, email="user@example.com", name="x" * 201, status="pending")


def test_send_options_default() -> None:
    options = SendOptions()
    assert options.delay_seconds == 4


def test_upload_response_structure() -> None:
    response = UploadResponse(message="Success", recipient_count=42)
    assert response.recipient_count == 42


def test_recipient_list_response_pagination_fields() -> None:
    response = RecipientListResponse(
        items=[RecipientItem(email="user@example.com", name="User")],
        page=2,
        page_size=20,
        total=41,
    )
    assert response.page == 2
    assert response.page_size == 20
    assert response.total == 41
    assert len(response.items) == 1


def test_recipient_stats_schema() -> None:
    from app.schemas.recipient import RecipientStats

    default_stats = RecipientStats()
    assert default_stats.total == 0
    assert default_stats.sent == 0
    assert default_stats.pending == 0
    assert default_stats.failed == 0

    custom_stats = RecipientStats(total=10, sent=7, pending=2, failed=1)
    assert custom_stats.total == 10
    assert custom_stats.sent == 7
    assert custom_stats.pending == 2
    assert custom_stats.failed == 1

    with pytest.raises(ValidationError):
        RecipientStats(total=-1)


def test_recipient_query_filter_schema() -> None:
    from app.schemas.recipient import RecipientQueryFilter

    default_filter = RecipientQueryFilter()
    assert default_filter.status is None
    assert default_filter.search is None

    custom_filter = RecipientQueryFilter(status="sent", search="alice")
    assert custom_filter.status == "sent"
    assert custom_filter.search == "alice"

    with pytest.raises(ValidationError):
        RecipientQueryFilter(search="x" * 101)


