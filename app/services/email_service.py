"""Email service implementations for synchronous and asynchronous outbound delivery."""

from __future__ import annotations

import smtplib
from email.message import EmailMessage

from app.core.config import settings


class EmailService:
    """Encapsulates outbound synchronous email delivery via SMTP."""

    def send_email(self, recipient: str, subject: str, body: str) -> None:
        """Construct and deliver a single email message via SMTP.

        Args:
            recipient: Target recipient email address.
            subject: Subject line string.
            body: Plaintext message body.
        """
        message = EmailMessage()
        message["From"] = settings.smtp_from_email
        message["To"] = recipient
        message["Subject"] = subject
        message.set_content(body)

        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=30) as server:
            server.starttls()
            server.login(settings.smtp_username, settings.smtp_password)
            server.send_message(message)


class AsyncEmailService:
    """Encapsulates outbound asynchronous email delivery via SMTP."""

    async def send_email(self, recipient: str, subject: str, body: str) -> None:
        """Asynchronously deliver a single email message via SMTP.

        Args:
            recipient: Target recipient email address.
            subject: Subject line string.
            body: Plaintext message body.
        """
        message = EmailMessage()
        message["From"] = settings.smtp_from_email
        message["To"] = recipient
        message["Subject"] = subject
        message.set_content(body)

        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=30) as server:
            server.starttls()
            server.login(settings.smtp_username, settings.smtp_password)
            server.send_message(message)