"""Celery tasks for asynchronous campaign sending."""

from __future__ import annotations

import logging
import smtplib
import time
import uuid
from datetime import datetime, timezone

from celery import Task
from sqlalchemy import select

from app.core.config import settings
from app.db.models import Campaign, CampaignStatus, EmailLog, Recipient, RecipientStatus
from app.db.session import SessionLocal
from app.services.email_service import EmailService
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)
email_service = EmailService()


def _render_message(template: str, name: str | None) -> str:
    safe_name = name or "there"
    return template.replace("{name}", safe_name)


@celery_app.task(
    bind=True,
    autoretry_for=(ConnectionError, TimeoutError, smtplib.SMTPException),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def send_campaign_emails(self: Task, campaign_id: str, delay_seconds: int | None = None) -> dict[str, str]:
    """Process pending recipients in a campaign and send emails one-by-one."""
    throttle = delay_seconds or settings.send_delay_seconds
    db = SessionLocal()
    cid = uuid.UUID(campaign_id)
    try:
        campaign = db.get(Campaign, cid)
        if not campaign:
            logger.error("Campaign missing: %s", campaign_id)
            return {"status": "missing_campaign"}

        pending_recipients = db.scalars(
            select(Recipient).where(Recipient.campaign_id == cid, Recipient.status == RecipientStatus.pending)
        ).all()

        for recipient in pending_recipients:
            try:
                body = _render_message(campaign.message, recipient.name)
                email_service.send_email(recipient.email, campaign.subject, body)
                recipient.status = RecipientStatus.sent
                recipient.sent_at = datetime.now(timezone.utc)
                recipient.error_message = None
                campaign.sent_count += 1
                db.add(EmailLog(recipient_id=recipient.id, status="sent", response="SMTP delivered"))
                db.commit()
                logger.info("Email sent campaign=%s recipient=%s", campaign.id, recipient.email)
            except Exception as exc:  # noqa: BLE001
                recipient.status = RecipientStatus.failed
                recipient.error_message = str(exc)
                campaign.failed_count += 1
                db.add(EmailLog(recipient_id=recipient.id, status="failed", response=str(exc)))
                db.commit()
                logger.exception("Email failed campaign=%s recipient=%s", campaign.id, recipient.email)

            time.sleep(throttle)

        campaign.status = CampaignStatus.completed
        db.commit()
        return {"status": "completed"}
    finally:
        db.close()
