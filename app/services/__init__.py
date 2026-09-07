"""Business logic services package."""

from __future__ import annotations

from app.services.campaign_service import (
    campaign_status_payload,
    create_campaign,
    ensure_can_send,
    get_campaign_or_404,
    latest_campaign_error,
    list_campaigns,
    mark_campaign_running,
    upload_recipients,
)
from app.services.csv_service import parse_recipients_csv
from app.services.email_service import AsyncEmailService, EmailService

__all__ = [
    "create_campaign",
    "latest_campaign_error",
    "get_campaign_or_404",
    "upload_recipients",
    "list_campaigns",
    "campaign_status_payload",
    "ensure_can_send",
    "mark_campaign_running",
    "parse_recipients_csv",
    "EmailService",
    "AsyncEmailService",
]
