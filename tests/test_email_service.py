"""Unit tests for EmailService and AsyncEmailService."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.core.config import settings
from app.services.email_service import AsyncEmailService, EmailService, _build_message


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
