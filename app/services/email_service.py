"""SMTP email sending service."""

from asyncio import protocols
from __future__ import annotations

import smtplib
from email.message import EmailMessage

from app.core.config import settings


class EmailService:
    """Encapsulates outbound email delivery implementation."""

    def send_email(self, recipient: str, subject: str, body: str) -> None:
        print(f"Sending email>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
        message = EmailMessage()
        message["From`"] = settings.smtp_from_email
        message["To"] = recipient
        message["Subject"] = subject
        message.set_content(body)

        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=30) as server:
            server.starttls()
            server.login(settings.smtp_username, settings.smtp_password)
            server.send_message(message)

class AsyncEmailService:
    async def send_email(self, recipient: str, subject: str, body: str) -> None:
        print(f"Sending email>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
        message = EmailMessage()
        message["From"] = settings.smtp_from_email
        message["To"] = recipient
        message["Subject"] = subject
        message.set_content(body)

        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=30) as server:
            server.starttls()
            server.login(settings.smtp_username, settings.smtp_password)
            server.send_message(message)