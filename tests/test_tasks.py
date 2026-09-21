"""Unit tests for Celery task helper functions."""

from __future__ import annotations

import logging
import smtplib
import uuid
from unittest.mock import MagicMock

from app.core.config import settings
from app.utils import mask_email
from app.workers.tasks import _dispatch_campaign_emails, _render_message, send_campaign_emails


def test_render_message_with_name() -> None:
    template = "Hello {name}, welcome to MailForge!"
    rendered = _render_message(template, "Alice")
    assert rendered == "Hello Alice, welcome to MailForge!"


def test_render_message_with_none_name() -> None:
    template = "Hello {name}, welcome!"
    rendered = _render_message(template, None)
    assert rendered == "Hello there, welcome!"


def test_render_message_without_placeholder() -> None:
    template = "Welcome to MailForge!"
    rendered = _render_message(template, "Bob")
    assert rendered == "Welcome to MailForge!"


def test_task_retry_configuration_uses_settings_limit() -> None:
    assert send_campaign_emails.retry_kwargs["max_retries"] == settings.max_retries_limit
    assert smtplib.SMTPException in send_campaign_emails.autoretry_for
    assert send_campaign_emails.retry_backoff is True


def test_dispatch_campaign_emails_logs_masked_emails(caplog, monkeypatch) -> None:
    from app.db.models import Campaign, Recipient, RecipientStatus
    from app.workers import tasks

    campaign = MagicMock(spec=Campaign)
    campaign.id = uuid.uuid4()
    campaign.subject = "Subject"
    campaign.message = "Hello {name}"
    campaign.sent_count = 0
    campaign.failed_count = 0

    recipient = MagicMock(spec=Recipient)
    recipient.id = 1
    recipient.email = "alice@example.com"
    recipient.name = "Alice"
    recipient.status = RecipientStatus.pending

    db = MagicMock()
    monkeypatch.setattr(tasks.email_service, "send_email", lambda *args, **kwargs: None)

    with caplog.at_level(logging.INFO, logger="app.workers.tasks"):
        _dispatch_campaign_emails(db, campaign, [recipient], throttle=0)

    assert "alice@example.com" not in caplog.text
    assert mask_email("alice@example.com") in caplog.text
    assert recipient.status == RecipientStatus.sent
    assert campaign.sent_count == 1


def test_dispatch_campaign_emails_skips_throttle_after_last_recipient(monkeypatch) -> None:
    from app.db.models import Campaign, Recipient, RecipientStatus
    from app.workers import tasks

    campaign = MagicMock(spec=Campaign)
    campaign.id = uuid.uuid4()
    campaign.subject = "Subject"
    campaign.message = "Hello {name}"
    campaign.sent_count = 0
    campaign.failed_count = 0

    recipients = []
    for i in range(3):
        recipient = MagicMock(spec=Recipient)
        recipient.id = i + 1
        recipient.email = f"user{i}@example.com"
        recipient.name = f"User{i}"
        recipient.status = RecipientStatus.pending
        recipients.append(recipient)

    db = MagicMock()
    sleep_calls = {"count": 0}

    def _fake_sleep(*_args):
        sleep_calls["count"] += 1

    monkeypatch.setattr(tasks.email_service, "send_email", lambda *args, **kwargs: None)
    monkeypatch.setattr(tasks.time, "sleep", _fake_sleep)

    _dispatch_campaign_emails(db, campaign, recipients, throttle=5)

    assert sleep_calls["count"] == 2
    assert campaign.sent_count == 3


def test_send_campaign_emails_missing_campaign(monkeypatch) -> None:
    from app.workers import tasks

    mock_db = MagicMock()
    mock_db.get.return_value = None
    monkeypatch.setattr(tasks, "SessionLocal", lambda: mock_db)

    result = tasks.send_campaign_emails.run(str(uuid.uuid4()), delay_seconds=0)

    assert result == {"status": "missing_campaign"}
    mock_db.close.assert_called_once()


def test_send_campaign_emails_invalid_campaign_id(monkeypatch) -> None:
    from app.workers import tasks

    mock_db = MagicMock()
    monkeypatch.setattr(tasks, "SessionLocal", lambda: mock_db)

    result = tasks.send_campaign_emails.run("not-a-uuid", delay_seconds=0)

    assert result == {"status": "failed"}
    assert mock_db.get.call_count == 0
    mock_db.close.assert_called_once()


def test_send_campaign_emails_no_pending_recipients(monkeypatch) -> None:
    from app.db.models import Campaign, CampaignStatus
    from app.workers import tasks

    campaign = MagicMock(spec=Campaign)
    campaign.id = uuid.uuid4()

    db = MagicMock()
    db.get.return_value = campaign
    db.scalars.return_value.all.return_value = []
    monkeypatch.setattr(tasks, "SessionLocal", lambda: db)
    monkeypatch.setattr(tasks.email_service, "send_email", lambda *a, **k: None)
    monkeypatch.setattr(tasks.time, "sleep", lambda *a, **k: None)

    result = tasks.send_campaign_emails.run(str(campaign.id), delay_seconds=0)

    assert result == {"status": "completed"}
    assert campaign.status == CampaignStatus.completed
    assert db.commit.call_count == 1
    db.close.assert_called_once()


def test_send_campaign_emails_completed_flow(monkeypatch) -> None:
    from app.db.models import Campaign, RecipientStatus
    from app.workers import tasks

    campaign = MagicMock(spec=Campaign)
    campaign.id = uuid.uuid4()
    campaign.subject = "Hello"
    campaign.message = "Hi {name}"
    campaign.sent_count = 0
    campaign.failed_count = 0

    recipient = MagicMock()
    recipient.id = 1
    recipient.email = "bob@example.com"
    recipient.name = "Bob"
    recipient.status = RecipientStatus.pending

    db = MagicMock()
    db.get.return_value = campaign
    db.scalars.return_value.all.return_value = [recipient]
    monkeypatch.setattr(tasks, "SessionLocal", lambda: db)
    monkeypatch.setattr(tasks.email_service, "send_email", lambda *a, **k: None)
    monkeypatch.setattr(tasks.time, "sleep", lambda *a, **k: None)

    result = tasks.send_campaign_emails.run(str(campaign.id), delay_seconds=0)

    assert result == {"status": "completed"}
    assert recipient.status == RecipientStatus.sent
    assert campaign.sent_count == 1
    assert campaign.status.value == "completed"
    assert db.commit.call_count >= 2
    db.close.assert_called_once()
