"""Email service implementations for synchronous and asynchronous outbound delivery."""

from __future__ import annotations

import logging
import smtplib
import time
from email.message import EmailMessage

from app.core.config import settings
from app.utils import sanitize_subject

logger = logging.getLogger(__name__)


def _build_message(recipient: str, subject: str, body: str) -> EmailMessage:
    """Construct a plaintext email message with the configured sender.

    The subject is sanitized to strip line breaks, preventing SMTP header
    injection via crafted campaign subject lines.

    Args:
        recipient: Target recipient email address.
        subject: Subject line string.
        body: Plaintext message body.

    Returns:
        Populated EmailMessage ready for delivery.
    """
    message = EmailMessage()
    message["From"] = settings.smtp_from_email
    message["To"] = recipient
    message["Subject"] = sanitize_subject(subject)
    message.set_content(body)
    return message


def _send_with_retry(message: EmailMessage) -> None:
    """Deliver a message via SMTP with bounded retries on transient errors.

    Args:
        message: EmailMessage instance to deliver.

    Raises:
        smtplib.SMTPException: If delivery fails after configured retry count.
    """
    last_error: Exception | None = None
    for attempt in range(settings.retry_count + 1):
        try:
            with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=30) as server:
                server.starttls()
                server.login(settings.smtp_username, settings.smtp_password)
                server.send_message(message)
            return
        except smtplib.SMTPException as exc:
            last_error = exc
            if attempt >= settings.retry_count:
                break
            time.sleep(min(2**attempt, 4))

    if last_error is not None:
        raise last_error


class EmailService:
    """Encapsulates outbound synchronous email delivery via SMTP."""

    def send_email(self, recipient: str, subject: str, body: str) -> None:
        """Construct and deliver a single email message via SMTP.

        Args:
            recipient: Target recipient email address.
            subject: Subject line string.
            body: Plaintext message body.
        """
        _send_with_retry(_build_message(recipient, subject, body))


class AsyncEmailService:
    """Encapsulates outbound asynchronous email delivery via SMTP."""

    async def send_email(self, recipient: str, subject: str, body: str) -> None:
        """Asynchronously deliver a single email message via SMTP.

        Args:
            recipient: Target recipient email address.
            subject: Subject line string.
            body: Plaintext message body.
        """
        _send_with_retry(_build_message(recipient, subject, body))