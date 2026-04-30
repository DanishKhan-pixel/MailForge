"""Email sending service using SMTP with retries and delays."""

from __future__ import annotations

import logging
import smtplib
import time
from email.message import EmailMessage

from app.services.state_service import complete_run, mark_failure, mark_success, state
from app.utils.config import settings
from app.utils.template import render_template

logger = logging.getLogger(__name__)


def _send_single_email(recipient: str, subject: str, body: str) -> None:
    """Connect to SMTP and send a single personalized message."""
    email_message = EmailMessage()
    email_message["From"] = settings.smtp_from_email
    email_message["To"] = recipient
    email_message["Subject"] = subject
    email_message.set_content(body)

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=30) as server:
        server.starttls()
        server.login(settings.smtp_username, settings.smtp_password)
        server.send_message(email_message)


def send_emails_in_background(subject: str, message_template: str, delay_seconds: int) -> None:
    """Send uploaded emails sequentially in a background task."""
    recipients = list(state.recipients)
    logger.info("Starting email run. recipients=%d", len(recipients))

    try:
        for index, row in enumerate(recipients, start=1):
            recipient_email = row["email"]
            rendered_message = render_template(message_template, row)

            sent = False
            last_exception: Exception | None = None

            for attempt in range(1, settings.retry_count + 2):
                try:
                    _send_single_email(recipient_email, subject, rendered_message)
                    sent = True
                    mark_success()
                    logger.info("Email sent. recipient=%s index=%d", recipient_email, index)
                    break
                except Exception as exc:  # noqa: BLE001 - log and continue is intentional.
                    last_exception = exc
                    logger.warning(
                        "Send attempt failed. recipient=%s attempt=%d error=%s",
                        recipient_email,
                        attempt,
                        str(exc),
                    )
                    # Small pause before retry to avoid immediate repeated failures.
                    time.sleep(1)

            if not sent:
                error_message = f"Failed for {recipient_email}: {last_exception}"
                mark_failure(error_message)
                logger.error(error_message)

            # Throttle every email send to avoid spam-like bursts.
            if index < len(recipients):
                time.sleep(delay_seconds)
    finally:
        complete_run()
        logger.info("Email run completed.")
