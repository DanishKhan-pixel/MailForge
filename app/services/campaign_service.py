"""Campaign orchestration business logic."""

from app.db import models
from __future__ import annotations

import logging
import uuid

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import Campaign, CampaignStatus, Recipient, RecipientStatus

logger = logging.getLogger(__name__)


def create_campaign(db: Session, subject: str, message: str) -> Campaign:
    campaign = Campaign(subject=subject, message=message)
    db.add(campaign)
    db.commit()
    db.refresh(campaign)
    return campaign

def name():
    """
    Purpose: 
    """
    
# end def

def get_campaign_or_404(db: Session, campaign_id: uuid.UUID) -> Campaign:
    campaign = db.get(Campaign, campaign_id)
    if not campaign:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found.")
    return campaign


def upload_recipients(db: Session, campaign: Campaign, rows: list[dict[str, str]]) -> int:
    recipients = [Recipient(campaign_id=campaign.id, email=row["email"], name=row["name"] or None) for row in rows]
    db.add_all(recipients)
    campaign.total_emails = campaign.total_emails + len(recipients)
    db.commit()
    return len(recipients)


def list_campaigns(
    db: Session, page: int, page_size: int, status_filter: str | None
) -> tuple[list[Campaign], int]:
    query = select(Campaign).order_by(Campaign.created_at.desc())
    count_query = select(func.count(Campaign.id))
    if status_filter:
        query = query.where(Campaign.status == status_filter)
        count_query = count_query.where(Campaign.status == status_filter)

    total = db.scalar(count_query) or 0
    campaigns = db.scalars(query.offset((page - 1) * page_size).limit(page_size)).all()
    return campaigns, total


def campaign_status_payload(campaign: Campaign, last_error: str | None = None) -> dict[str, object]:
    pending_count = max(campaign.total_emails - campaign.sent_count - campaign.failed_count, 0)
    progress_percent = 0.0
    if campaign.total_emails > 0:
        progress_percent = round(((campaign.sent_count + campaign.failed_count) / campaign.total_emails) * 100, 2)
    return {
        "campaign_id": campaign.id,
        "status": campaign.status.value if isinstance(campaign.status, CampaignStatus) else str(campaign.status),
        "total_emails": campaign.total_emails,
        "sent_count": campaign.sent_count,
        "failed_count": campaign.failed_count,
        "pending_count": pending_count,
        "progress_percent": progress_percent,
        "last_error": last_error,
    }


def ensure_can_send(campaign: Campaign) -> None:
    if campaign.total_emails == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Upload recipients before sending.")
    if campaign.status == CampaignStatus.running:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Campaign is already running.")


def mark_campaign_running(db: Session, campaign: Campaign) -> None:
    campaign.status = CampaignStatus.running
    db.commit()
