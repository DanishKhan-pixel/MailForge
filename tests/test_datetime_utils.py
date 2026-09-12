"""Unit tests for datetime formatting and parsing utilities."""

from __future__ import annotations

from datetime import datetime, timezone

from app.utils.datetime_utils import format_utc_timestamp, parse_iso_timestamp


def test_format_utc_timestamp_default() -> None:
    formatted = format_utc_timestamp()
    assert isinstance(formatted, str)
    assert "+00:00" in formatted or "Z" in formatted or "T" in formatted


def test_format_utc_timestamp_specific() -> None:
    dt = datetime(2026, 9, 13, 12, 0, 0, tzinfo=timezone.utc)
    formatted = format_utc_timestamp(dt)
    assert "2026-09-13T12:00:00" in formatted


def test_parse_iso_timestamp() -> None:
    iso_str = "2026-09-13T12:00:00+00:00"
    parsed = parse_iso_timestamp(iso_str)
    assert parsed.year == 2026
    assert parsed.month == 9
    assert parsed.day == 13
    assert parsed.tzinfo == timezone.utc
