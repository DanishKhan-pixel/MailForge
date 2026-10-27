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


def test_campaign_model_has_updated_at_timestamp() -> None:
    cid = uuid.uuid4()
    campaign = Campaign(id=cid, subject="Welcome", message="Hello")
    assert campaign.updated_at is None

    column = Campaign.__table__.columns.get("updated_at")
    assert column is not None
    assert column.server_default is not None
    assert column.onupdate is not None


def test_recipient_model_repr() -> None:
    cid = uuid.uuid4()
    recipient = Recipient(id=1, campaign_id=cid, email="test@example.com", status=RecipientStatus.pending)
    repr_str = repr(recipient)
    assert "id=1" in repr_str
    assert "email='test@example.com'" in repr_str


def test_recipient_is_sent() -> None:
    cid = uuid.uuid4()
    sent_recipient = Recipient(id=1, campaign_id=cid, email="test@example.com", status=RecipientStatus.sent)
    assert sent_recipient.is_sent is True

    pending_recipient = Recipient(id=2, campaign_id=cid, email="test@example.com", status=RecipientStatus.pending)
    assert pending_recipient.is_sent is False


def test_recipient_display_name() -> None:
    cid = uuid.uuid4()
    named = Recipient(id=1, campaign_id=cid, email="user@example.com", name="  Alice Wonderland  ")
    assert named.display_name == "Alice Wonderland"

    unnamed = Recipient(id=2, campaign_id=cid, email="anon@example.com", name="")
    assert unnamed.display_name == "anon@example.com"

    none_named = Recipient(id=3, campaign_id=cid, email="anon2@example.com", name=None)
    assert none_named.display_name == "anon2@example.com"




def test_email_log_model_repr() -> None:
    log = EmailLog(id=10, recipient_id=1, status="sent")
    repr_str = repr(log)
    assert "id=10" in repr_str
    assert "status='sent'" in repr_str


def test_email_log_is_success() -> None:
    sent_log = EmailLog(id=1, recipient_id=1, status="sent")
    assert sent_log.is_success is True

    failed_log = EmailLog(id=2, recipient_id=1, status="failed")
    assert failed_log.is_success is False



def test_recipient_has_case_insensitive_unique_index() -> None:
    index_names = {index.name for index in Recipient.__table__.indexes}
    assert "uq_recipients_campaign_email" in index_names
    unique_index = next(index for index in Recipient.__table__.indexes if index.name == "uq_recipients_campaign_email")
    assert unique_index.unique is True


def test_recipient_has_campaign_status_composite_index() -> None:
    index = next(index for index in Recipient.__table__.indexes if index.name == "ix_recipients_campaign_status")
    assert {column.name for column in index.columns} == {"campaign_id", "status"}


def test_campaign_progress_percentage() -> None:
    c_zero = Campaign(subject="Test", message="Body", total_emails=0)
    assert c_zero.progress_percentage == 0.0

    c_half = Campaign(subject="Test", message="Body", total_emails=10, sent_count=3, failed_count=2)
    assert c_half.progress_percentage == 50.0

    c_full = Campaign(subject="Test", message="Body", total_emails=4, sent_count=4, failed_count=0)
    assert c_full.progress_percentage == 100.0


def test_campaign_is_finished() -> None:
    pending = Campaign(subject="Test", message="Body", status=CampaignStatus.pending)
    assert pending.is_finished is False

    running = Campaign(subject="Test", message="Body", status=CampaignStatus.running)
    assert running.is_finished is False

    completed = Campaign(subject="Test", message="Body", status=CampaignStatus.completed)
    assert completed.is_finished is True


