"""Unit tests for email parsing utilities."""

from __future__ import annotations

from app.utils.email_utils import extract_email_domain


def test_extract_email_domain_valid() -> None:
    assert extract_email_domain("user@example.com") == "example.com"
    assert extract_email_domain("alice@Sub.Domain.ORG") == "sub.domain.org"


def test_extract_email_domain_invalid() -> None:
    assert extract_email_domain("notanemail") is None
    assert extract_email_domain("user@") is None
    assert extract_email_domain("@domain.com") is None
    assert extract_email_domain("") is None
