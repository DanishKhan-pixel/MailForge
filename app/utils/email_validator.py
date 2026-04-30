"""Helpers for validating email addresses."""

import re

# Basic but reliable email syntax check.
EMAIL_REGEX = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")


def is_valid_email(value: str) -> bool:
    """Return True when the provided string matches email format."""
    return bool(EMAIL_REGEX.match(value.strip()))
