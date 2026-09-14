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
