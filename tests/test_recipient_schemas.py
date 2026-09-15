"""Unit tests for recipient Pydantic schemas."""

from __future__ import annotations

from app.schemas.recipient import RecipientItem, RecipientListResponse, SendOptions, UploadResponse


def test_recipient_item_valid() -> None:
    item = RecipientItem(email="user@example.com", name="User Name")
    assert item.email == "user@example.com"
    assert item.name == "User Name"


def test_recipient_item_optional_name() -> None:
    item = RecipientItem(email="user@example.com")
    assert item.email == "user@example.com"
    assert item.name is None


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
