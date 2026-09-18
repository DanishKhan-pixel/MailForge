"""Unit tests for EmailPayload Pydantic schema."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.schemas.recipient import EmailPayload


def test_email_payload_valid() -> None:
    payload = EmailPayload(recipient="user@example.com", subject="Welcome", body="Hello World")
    assert payload.recipient == "user@example.com"
    assert payload.subject == "Welcome"
    assert payload.body == "Hello World"


def test_email_payload_validation_empty_subject() -> None:
    with pytest.raises(ValidationError):
        EmailPayload(recipient="user@example.com", subject="", body="Hello World")


def test_email_payload_validation_empty_body() -> None:
    with pytest.raises(ValidationError):
        EmailPayload(recipient="user@example.com", subject="Welcome", body="")


def test_email_payload_validation_invalid_recipient() -> None:
    with pytest.raises(ValidationError):
        EmailPayload(recipient="not-an-email", subject="Welcome", body="Hello")
