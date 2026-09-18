"""Unit tests for EmailService and AsyncEmailService."""

from __future__ import annotations

import smtplib
from unittest.mock import MagicMock, patch

import pytest

from app.core.config import settings
from app.services.email_service import AsyncEmailService, EmailService, _build_message


@patch("smtplib.SMTP")
def test_send_email_uses_configured_smtp_timeout(mock_smtp_cls: MagicMock) -> None:
    mock_smtp_instance = MagicMock()
    mock_smtp_cls.return_value.__enter__.return_value = mock_smtp_instance

    service = EmailService()
    service.send_email(recipient="user@example.com", subject="Test Subject", body="Test Body")

    mock_smtp_cls.assert_called_once_with(settings.smtp_host, settings.smtp_port, timeout=settings.smtp_timeout)


@patch("smtplib.SMTP")
def test_send_email_sync(mock_smtp_cls: MagicMock) -> None:
    mock_smtp_instance = MagicMock()
    mock_smtp_cls.return_value.__enter__.return_value = mock_smtp_instance

    service = EmailService()
    service.send_email(recipient="user@example.com", subject="Test Subject", body="Test Body")

    mock_smtp_instance.starttls.assert_called_once()
    mock_smtp_instance.login.assert_called_once()
    mock_smtp_instance.send_message.assert_called_once()


@pytest.mark.asyncio
@patch("smtplib.SMTP")
async def test_send_email_async(mock_smtp_cls: MagicMock) -> None:
    mock_smtp_instance = MagicMock()
    mock_smtp_cls.return_value.__enter__.return_value = mock_smtp_instance

    service = AsyncEmailService()
    await service.send_email(recipient="user@example.com", subject="Async Subject", body="Async Body")

    mock_smtp_instance.starttls.assert_called_once()
    mock_smtp_instance.login.assert_called_once()
    mock_smtp_instance.send_message.assert_called_once()


def test_build_message_composition() -> None:
    message = _build_message(recipient="user@example.com", subject="Subject", body="Body")

    assert message["From"] == settings.smtp_from_email
    assert message["To"] == "user@example.com"
    assert message["Subject"] == "Subject"
    assert message.get_content().strip() == "Body"


def test_build_message_sanitizes_subject_against_header_injection() -> None:
    crafted = "Legit Subject\r\nBcc: attacker@example.com"
    message = _build_message(recipient="user@example.com", subject=crafted, body="Body")

    assert "\r" not in message["Subject"]
    assert "\n" not in message["Subject"]
    assert "Bcc" not in message
    assert message["Subject"] == "Legit Subject Bcc: attacker@example.com"


def test_send_email_retries_on_transient_smtp_failure(monkeypatch) -> None:
    from app.services import email_service

    attempts = {"count": 0}

    def _fake_smtp(*args, **kwargs):
        attempts["count"] += 1
        inst = MagicMock()
        if attempts["count"] <= 1:
            inst.__enter__.side_effect = smtplib.SMTPException("temporary")
        else:
            inst.__enter__.return_value = inst
        return inst

    monkeypatch.setattr(email_service.time, "sleep", lambda *_a: None)
    with patch("smtplib.SMTP", side_effect=_fake_smtp):
        with patch.object(email_service.settings, "retry_count", 1):
            service = EmailService()
            service.send_email(recipient="user@example.com", subject="S", body="B")

    assert attempts["count"] == 2


def test_send_email_exhausts_retries_on_persistent_failure() -> None:
    from app.services import email_service

    def _always_fail(*args, **kwargs):
        inst = MagicMock()
        inst.__enter__.side_effect = smtplib.SMTPException("down")
        return inst

    with patch("smtplib.SMTP", side_effect=_always_fail):
        with patch.object(email_service.settings, "retry_count", 1):
            with patch.object(email_service.time, "sleep", lambda *_a: None):
                service = EmailService()
                with pytest.raises(smtplib.SMTPException, match="down"):
                    service.send_email(recipient="user@example.com", subject="S", body="B")
