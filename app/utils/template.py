"""Utilities for safe string templating with CSV row data."""

from collections import defaultdict


def render_template(template: str, payload: dict[str, str]) -> str:
    """
    Render a format-style template string.

    Uses a safe default for missing keys so the process keeps running
    instead of crashing on a missing placeholder.
    """
    safe_payload = defaultdict(str, payload)
    return template.format_map(safe_payload)
