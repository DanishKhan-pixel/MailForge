"""Unit tests for EmailService and AsyncEmailService."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.services.email_service import AsyncEmailService, EmailService


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
