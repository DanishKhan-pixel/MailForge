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


def sanitize_subject(subject: str) -> str:
    """Sanitize email subject string by stripping outer whitespace and replacing line breaks.

    Args:
        subject: Raw email subject line input.

    Returns:
        Sanitized single-line email subject string.
    """
    if not subject:
        return ""
    clean = subject.replace("\r", "").replace("\n", " ").strip()
    return " ".join(clean.split())


def strip_html_tags(text: str) -> str:
    """Remove HTML tags from a text string and return plain text.

    Args:
        text: Raw text or HTML input string.

    Returns:
        Clean plain text with tags stripped.
    """
    if not text:
        return ""
    import re

    clean = re.sub(r"<[^>]*>", "", text)
    return " ".join(clean.split())


def normalize_email(email: str) -> str:
    """Normalize email address by stripping whitespace and lowercasing domain.

    Args:
        email: Raw email address string.

    Returns:
        Normalized email string with lowercased domain.
    """
    if not email:
        return ""
    clean = email.strip()
    if "@" in clean:
        local_part, domain = clean.rsplit("@", 1)
        return f"{local_part}@{domain.lower()}"
    return clean.lower()
