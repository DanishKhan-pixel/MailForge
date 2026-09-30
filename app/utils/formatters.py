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


def format_file_size(size_bytes: int) -> str:
    """Format raw byte size into a human-readable string representation.

    Args:
        size_bytes: Non-negative integer count of bytes.

    Returns:
        Formatted file size string (e.g. '500 B', '1.5 KB', '2.0 MB').
    """
    if size_bytes < 0:
        return "0 B"

    size = float(size_bytes)
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024.0 or unit == "GB":
            if unit == "B":
                return f"{int(size)} B"
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size_bytes} B"
