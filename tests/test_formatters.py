"""Unit tests for string formatting and email masking utilities."""

from __future__ import annotations

from app.utils.formatters import mask_email


def test_mask_email_standard() -> None:
    assert mask_email("alice@example.com") == "a***e@example.com"


def test_mask_email_short_username() -> None:
    assert mask_email("ab@example.com") == "a*@example.com"
    assert mask_email("a@example.com") == "a*@example.com"


def test_mask_email_invalid_string() -> None:
    assert mask_email("notanemail") == "notanemail"
    assert mask_email("") == ""
