"""Campaign orchestration business logic."""

from __future__ import annotations

import logging
import uuid

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import Campaign, CampaignStatus, Recipient, RecipientStatus

logger = logging.getLogger(__name__)


def create_campaign(db: Session, subject: str, message: str) -> Campaign:
    """Create and persist a new Campaign instance in the database.

    Args:
        db: Active SQLAlchemy database session.
        subject: Subject line for the email campaign.
        message: Template message content for the emails.

    Returns:
        The newly created Campaign object.
    """
    campaign = Campaign(subject=subject, message=message)
    db.add(campaign)
    db.commit()
    db.refresh(campaign)
    return campaign


def latest_campaign_error(db: Session, campaign_id: uuid.UUID) -> str | None:
    """Retrieve the error message from the most recently failed recipient for a campaign.

    Args:
        db: Active SQLAlchemy database session.
        campaign_id: UUID of the target campaign.

    Returns:
        Error message string if found, otherwise None.
    """
    query = (
        select(Recipient.error_message)
        .where(
            Recipient.campaign_id == campaign_id,
            Recipient.status == RecipientStatus.failed,
            Recipient.error_message.isnot(None),
        )
        .order_by(Recipient.id.desc())
        .limit(1)
    )
    return db.scalar(query)


def get_campaign_or_404(db: Session, campaign_id: uuid.UUID) -> Campaign:
    """Retrieve a campaign by UUID or raise a 404 HTTP exception if not found.

    Args:
        db: Active SQLAlchemy database session.
        campaign_id: UUID of the target campaign.

    Returns:
        The matching Campaign object.

    Raises:
        HTTPException: 404 NOT FOUND if campaign does not exist.
    """
    campaign = db.get(Campaign, campaign_id)
    if not campaign:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found.")
    return campaign


def upload_recipients(db: Session, campaign: Campaign, rows: list[dict[str, str]]) -> int:
    """Bulk insert recipient records for a campaign and update recipient total.

    Args:
        db: Active SQLAlchemy database session.
        campaign: Target Campaign object.
        rows: List of recipient dictionaries containing 'email' and optional 'name'.

    Returns:
        Count of recipients added.
    """
    recipients = [Recipient(campaign_id=campaign.id, email=row["email"], name=row["name"] or None) for row in rows]
    db.add_all(recipients)
    campaign.total_emails = campaign.total_emails + len(recipients)
    db.commit()
    return len(recipients)


def list_campaigns(
    db: Session, page: int, page_size: int, status_filter: str | None
) -> tuple[list[Campaign], int]:
    """Retrieve a paginated list of campaigns filtered by status.

    Args:
        db: Active SQLAlchemy database session.
        page: 1-indexed page number.
        page_size: Number of records per page.
        status_filter: Optional campaign status filter string.

    Returns:
        Tuple containing (list of Campaign objects, total matching count).
    """
    query = select(Campaign).order_by(Campaign.created_at.desc())
    count_query = select(func.count(Campaign.id))
    if status_filter:
        query = query.where(Campaign.status == status_filter)
        count_query = count_query.where(Campaign.status == status_filter)

    total = db.scalar(count_query) or 0
    campaigns = db.scalars(query.offset((page - 1) * page_size).limit(page_size)).all()
    return campaigns, total


def campaign_status_payload(campaign: Campaign, last_error: str | None = None) -> dict[str, object]:
    """Calculate and construct status telemetry summary for a campaign.

    Args:
        campaign: Campaign model instance.
        last_error: Optional error message from last failed email.

    Returns:
        Dictionary containing calculated campaign progress and statistics.
    """
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
    """Validate that a campaign is in a valid state to initiate sending.

    Args:
        campaign: Target Campaign object.

    Raises:
        HTTPException: 400 BAD REQUEST if no recipients, 409 CONFLICT if already running.
    """
    if campaign.total_emails == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Upload recipients before sending.")
    if campaign.status == CampaignStatus.running:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Campaign is already running.")


def mark_campaign_running(db: Session, campaign: Campaign) -> None:
    """Update campaign status to running and commit to database.

    Args:
        db: Active SQLAlchemy database session.
        campaign: Target Campaign object.
    """
    campaign.status = CampaignStatus.running
    db.commit()

