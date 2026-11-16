"""Unit tests for campaign creation Pydantic schema."""

from __future__ import annotations

from app.schemas.campaign import CampaignCreate


def test_campaign_create_valid() -> None:
    payload = CampaignCreate(subject="Welcome", message="Hello {name}")
    assert payload.subject == "Welcome"
    assert payload.message == "Hello {name}"


def test_campaign_create_sanitizes_subject_line_breaks() -> None:
    payload = CampaignCreate(subject="Hello\r\nBcc: attacker@example.com", message="Body")
    assert "\r" not in payload.subject
    assert "\n" not in payload.subject
    assert payload.subject == "Hello Bcc: attacker@example.com"


def test_campaign_create_sanitizes_subject_whitespace() -> None:
    payload = CampaignCreate(subject="   Spaced Subject   ", message="Body")
    assert payload.subject == "Spaced Subject"


def test_campaign_create_rejects_empty_subject_after_sanitize() -> None:
    import pytest
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        CampaignCreate(subject="   ", message="Body")


def test_campaign_duplicate_schema() -> None:
    from app.schemas.campaign import CampaignDuplicate

    default_dup = CampaignDuplicate()
    assert default_dup.new_subject is None

    custom_dup = CampaignDuplicate(new_subject="Custom Subject")
    assert custom_dup.new_subject == "Custom Subject"

    sanitized = CampaignDuplicate(new_subject="Spaced\r\nSubject")
    assert sanitized.new_subject == "Spaced Subject"