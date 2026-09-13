"""Unit tests for string processing and truncation utilities."""

from __future__ import annotations

from app.utils.string_utils import truncate_text


def test_truncate_text_short() -> None:
    assert truncate_text("Hello World", max_length=50) == "Hello World"


def test_truncate_text_long() -> None:
    text = "This is a long message that needs to be truncated for display purposes."
    truncated = truncate_text(text, max_length=20)
    assert len(truncated) == 20
    assert truncated.endswith("...")
    assert truncated == "This is a long me..."


def test_truncate_text_custom_suffix() -> None:
    text = "Welcome to MailForge system!"
    truncated = truncate_text(text, max_length=15, suffix=" [more]")
    assert truncated.endswith(" [more]")
    assert len(truncated) == 15


def test_truncate_text_empty() -> None:
    assert truncate_text("") == ""
