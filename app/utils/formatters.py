"""Text formatting and masking utilities for application privacy and logging."""

from __future__ import annotations


def mask_email(email: str) -> str:
    """Mask email address username for privacy protection in logs.

    Args:
        email: Raw email address string (e.g. 'alice@example.com').

    Returns:
        Masked email string (e.g. 'a***e@example.com').
    """
    if not email or "@" not in email:
        return email

    username, domain = email.split("@", 1)
    if len(username) <= 2:
        masked_username = f"{username[0]}*" if username else "*"
    else:
        masked_username = f"{username[0]}{'*' * (len(username) - 2)}{username[-1]}"

    return f"{masked_username}@{domain}"
