"""Datetime formatting and parsing helper utilities."""

from __future__ import annotations

from datetime import datetime, timezone


def format_utc_timestamp(dt: datetime | None = None) -> str:
    """Format a datetime object into an ISO 8601 UTC string.

    Args:
        dt: Target datetime instance. Defaults to current UTC time if None.

    Returns:
        ISO formatted string representation in UTC.
    """
    target = dt or datetime.now(timezone.utc)
    if target.tzinfo is None:
        target = target.replace(tzinfo=timezone.utc)
    return target.astimezone(timezone.utc).isoformat()


def parse_iso_timestamp(timestamp_str: str) -> datetime:
    """Parse an ISO 8601 formatted timestamp string into a timezone-aware datetime.

    Args:
        timestamp_str: ISO formatted timestamp string.

    Returns:
        Timezone-aware datetime instance in UTC.
    """
    dt = datetime.fromisoformat(timestamp_str)
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)
