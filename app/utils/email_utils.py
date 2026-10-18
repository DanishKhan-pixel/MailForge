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


def is_valid_email_domain(domain: str) -> bool:
    """Validate whether a string is a properly formatted domain name.

    Args:
        domain: Input domain name string.

    Returns:
        True if valid domain structure with TLD, False otherwise.
    """
    if not domain or "." not in domain:
        return False
    parts = domain.strip().split(".")
    if len(parts) < 2 or any(not part for part in parts):
        return False
    return all(part.isalnum() or "-" in part for part in parts)


def format_recipient_display(name: str | None, email: str) -> str:
    """Format recipient name and email into standard email address display string.

    Args:
        name: Optional recipient display name.
        email: Recipient email address string.

    Returns:
        Formatted string like 'Jane Doe <jane@example.com>' or 'jane@example.com'.
    """
    clean_email = email.strip() if email else ""
    if name and name.strip():
        return f"{name.strip()} <{clean_email}>"
    return clean_email

