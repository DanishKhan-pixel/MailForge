"""String processing and manipulation helper utilities."""

from __future__ import annotations


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate text string to a maximum length with an optional suffix.

    Args:
        text: Input string to truncate.
        max_length: Maximum allowed character length including suffix.
        suffix: Suffix string appended when text is truncated.

    Returns:
        Truncated text string.
    """
    if not text or len(text) <= max_length:
        return text

    if max_length <= len(suffix):
        return suffix[:max_length]

    content_length = max_length - len(suffix)
    return f"{text[:content_length]}{suffix}"
