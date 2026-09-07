"""Background worker package."""

from __future__ import annotations

from app.workers.celery_app import celery_app
from app.workers.tasks import send_campaign_emails

__all__ = ["celery_app", "send_campaign_emails"]
