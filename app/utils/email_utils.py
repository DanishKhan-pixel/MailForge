"""Email parsing and validation helper utilities."""

from __future__ import annotations


def extract_email_domain(email: str) -> str | None:
    """Extract domain portion from an email address string.

    Args:
        email: Input email address string.

    Returns:
        Domain string in lowercase if valid, None otherwise.
    """
    if not email or "@" not in email:
        return None

    parts = email.strip().split("@")
    if len(parts) != 2 or not parts[0] or not parts[1]:
        return None

    return parts[1].lower()
