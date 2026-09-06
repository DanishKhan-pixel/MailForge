"""Unit tests for SQLAlchemy ORM models and status enums."""

from __future__ import annotations

import uuid

from app.db.models import (
    Campaign,
    CampaignStatus,
    EmailLog,
    Recipient,
    RecipientStatus,
)


def test_campaign_model_repr_and_defaults() -> None:
    cid = uuid.uuid4()
    campaign = Campaign(id=cid, subject="Welcome", message="Hello {name}", status=CampaignStatus.pending)
    repr_str = repr(campaign)
    assert f"id={cid}" in repr_str
    assert "subject='Welcome'" in repr_str
    assert campaign.status == CampaignStatus.pending


def test_recipient_model_repr() -> None:
    cid = uuid.uuid4()
    recipient = Recipient(id=1, campaign_id=cid, email="test@example.com", status=RecipientStatus.pending)
    repr_str = repr(recipient)
    assert "id=1" in repr_str
    assert "email='test@example.com'" in repr_str


def test_email_log_model_repr() -> None:
    log = EmailLog(id=10, recipient_id=1, status="sent")
    repr_str = repr(log)
    assert "id=10" in repr_str
    assert "status='sent'" in repr_str
