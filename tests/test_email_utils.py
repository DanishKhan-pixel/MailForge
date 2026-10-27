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


def test_is_valid_email_domain() -> None:
    from app.utils.email_utils import is_valid_email_domain

    assert is_valid_email_domain("example.com") is True
    assert is_valid_email_domain("sub.domain.co.uk") is True
    assert is_valid_email_domain("invalid") is False
    assert is_valid_email_domain("domain.") is False
    assert is_valid_email_domain("") is False
    assert is_valid_email_domain(None) is False


def test_format_recipient_display() -> None:
    from app.utils.email_utils import format_recipient_display

    assert format_recipient_display("Jane Doe", "jane@example.com") == "Jane Doe <jane@example.com>"
    assert format_recipient_display("  Bob Smith  ", "bob@example.com") == "Bob Smith <bob@example.com>"
    assert format_recipient_display(None, "alice@example.com") == "alice@example.com"
    assert format_recipient_display("", "alice@example.com") == "alice@example.com"
    assert format_recipient_display("   ", "alice@example.com") == "alice@example.com"


def test_is_disposable_email_domain() -> None:
    from app.utils.email_utils import is_disposable_email_domain

    assert is_disposable_email_domain("mailinator.com") is True
    assert is_disposable_email_domain("TempMail.COM") is True
    assert is_disposable_email_domain("gmail.com") is False
    assert is_disposable_email_domain("example.org") is False
    assert is_disposable_email_domain("") is False
    assert is_disposable_email_domain(None) is False


