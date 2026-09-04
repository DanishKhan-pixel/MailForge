"""Database ORM models package."""

from __future__ import annotations

from app.db.models.campaign import Campaign, CampaignStatus
from app.db.models.email_log import EmailLog
from app.db.models.recipient import Recipient, RecipientStatus

__all__ = [
    "Campaign",
    "CampaignStatus",
    "Recipient",
    "RecipientStatus",
    "EmailLog",
]

