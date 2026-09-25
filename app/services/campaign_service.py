"""Campaign orchestration business logic."""

from __future__ import annotations

import csv
import io
import logging
import uuid

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.models import Campaign, CampaignStatus, EmailLog, Recipient, RecipientStatus
from app.utils import chunk_list, truncate_text

logger = logging.getLogger(__name__)

RECIPIENT_UPLOAD_CHUNK_SIZE = 500


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


def update_campaign(
    db: Session,
    campaign: Campaign,
    subject: str | None = None,
    message: str | None = None,
) -> Campaign:
    """Apply optional field updates to an existing campaign.

    Only fields explicitly provided are modified.

    Args:
        db: Active SQLAlchemy database session.
        campaign: Target Campaign object to update.
        subject: Optional new subject line.
        message: Optional new message template.

    Returns:
        The updated Campaign object.
    """
    if subject is not None:
        campaign.subject = subject
    if message is not None:
        campaign.message = message
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


def get_campaign_recipient_or_404(db: Session, campaign_id: uuid.UUID, recipient_id: int) -> Recipient:
    """Retrieve a recipient by ID scoped to a campaign or raise a 404.

    Args:
        db: Active SQLAlchemy database session.
        campaign_id: Target campaign UUID.
        recipient_id: Recipient integer identifier.

    Returns:
        The matching Recipient object.

    Raises:
        HTTPException: 404 NOT FOUND if recipient is missing or belongs to another campaign.
    """
    recipient = db.get(Recipient, recipient_id)
    if not recipient or recipient.campaign_id != campaign_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipient not found for campaign.")
    return recipient


def retry_failed_recipients(db: Session, campaign: Campaign) -> int:
    """Reset failed recipients of a campaign back to pending for retry.

    Clears per-recipient error and sent metadata so a follow-up dispatch
    attempt can process them again.

    Args:
        db: Active SQLAlchemy database session.
        campaign: Target Campaign object.

    Returns:
        Number of recipients queued for retry.
    """
    failed_recipients = db.scalars(
        select(Recipient).where(
            Recipient.campaign_id == campaign.id,
            Recipient.status == RecipientStatus.failed,
        )
    ).all()
    for recipient in failed_recipients:
        recipient.status = RecipientStatus.pending
        recipient.error_message = None
        recipient.sent_at = None
    db.commit()
    return len(failed_recipients)


def delete_campaign_recipient(db: Session, campaign: Campaign, recipient: Recipient) -> None:
    """Remove a recipient from a campaign and reconcile aggregate counters.

    The campaign recipient total and the matching sent/failed tally are
    decremented so progress telemetry stays consistent after removal.

    Args:
        db: Active SQLAlchemy database session.
        campaign: Parent Campaign object.
        recipient: Recipient record to delete.
    """
    if recipient.status == RecipientStatus.sent:
        campaign.sent_count = max(campaign.sent_count - 1, 0)
    elif recipient.status == RecipientStatus.failed:
        campaign.failed_count = max(campaign.failed_count - 1, 0)
    campaign.total_emails = max(campaign.total_emails - 1, 0)
    db.delete(recipient)
    db.commit()


def upload_recipients(db: Session, campaign: Campaign, rows: list[dict[str, str]]) -> int:
    """Bulk insert recipient records for a campaign and update recipient total.

    Rows are inserted in bounded chunks and flushed incrementally so large CSV
    uploads do not grow the session identity map without limit. Rows whose email
    is already registered for the campaign are skipped instead of failing the
    whole upload, thanks to the unique (campaign_id, email) constraint.

    Args:
        db: Active SQLAlchemy database session.
        campaign: Target Campaign object.
        rows: List of recipient dictionaries containing 'email' and optional 'name'.

    Returns:
        Count of newly added recipients.
    """
    added = 0
    for chunk in chunk_list(rows, RECIPIENT_UPLOAD_CHUNK_SIZE):
        recipients = [
            Recipient(campaign_id=campaign.id, email=row["email"], name=row["name"] or None) for row in chunk
        ]
        try:
            db.add_all(recipients)
            db.flush()
            added += len(chunk)
        except IntegrityError:
            db.rollback()
            for row in chunk:
                db.add(Recipient(campaign_id=campaign.id, email=row["email"], name=row["name"] or None))
                try:
                    db.flush()
                    added += 1
                except IntegrityError:
                    db.rollback()
    campaign.total_emails = campaign.total_emails + added
    db.commit()
    return added


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
        "last_error": truncate_text(last_error, max_length=500) if last_error else None,
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


def delete_campaign(db: Session, campaign: Campaign) -> None:
    """Delete a campaign and its cascaded recipients and email logs.

    Args:
        db: Active SQLAlchemy database session.
        campaign: Target Campaign object.
    """
    db.delete(campaign)
    db.commit()


def get_campaign_recipients(
    db: Session,
    campaign_id: uuid.UUID,
    status_filter: str | None = None,
) -> list[Recipient]:
    """Retrieve all recipient records associated with a campaign.

    Args:
        db: Active SQLAlchemy database session.
        campaign_id: Target campaign UUID.
        status_filter: Optional recipient status filter string.

    Returns:
        List of Recipient objects belonging to the campaign.
    """
    conditions = [Recipient.campaign_id == campaign_id]
    if status_filter:
        conditions.append(Recipient.status == status_filter)
    query = select(Recipient).where(*conditions).order_by(Recipient.id.asc())
    return list(db.scalars(query).all())


def build_recipients_csv(recipients: list[Recipient]) -> str:
    """Serialize recipient records into a CSV payload string.

    Args:
        recipients: Recipient records to export.

    Returns:
        CSV text with an email/name/status header row and one row per recipient.
    """
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["email", "name", "status"])
    for recipient in recipients:
        status = recipient.status.value if isinstance(recipient.status, RecipientStatus) else str(recipient.status)
        writer.writerow([recipient.email, recipient.name or "", status])
    return buffer.getvalue()


def paginate_campaign_recipients(
    db: Session,
    campaign_id: uuid.UUID,
    page: int,
    page_size: int,
    status_filter: str | None = None,
    search: str | None = None,
) -> tuple[list[Recipient], int]:
    """Retrieve a paginated slice of recipients for a campaign with the total matching count.

    Pagination, optional status filtering, and keyword search are applied at the
    database level to avoid loading the full recipient list into memory for large
    campaigns.

    Args:
        db: Active SQLAlchemy database session.
        campaign_id: Target campaign UUID.
        page: 1-indexed page number.
        page_size: Number of records to return per page.
        status_filter: Optional recipient status filter string.
        search: Optional keyword matched against recipient email or name.

    Returns:
        Tuple containing (list of Recipient objects for the page, total matching count).
    """
    conditions = [Recipient.campaign_id == campaign_id]
    if status_filter:
        conditions.append(Recipient.status == status_filter)
    if search:
        term = f"%{search.strip()}%"
        conditions.append(or_(Recipient.email.ilike(term), Recipient.name.ilike(term)))
    total = db.scalar(select(func.count(Recipient.id)).where(*conditions)) or 0
    query = (
        select(Recipient)
        .where(*conditions)
        .order_by(Recipient.id.asc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return list(db.scalars(query).all()), total


def paginate_campaign_logs(
    db: Session,
    campaign_id: uuid.UUID,
    page: int,
    page_size: int,
    status_filter: str | None = None,
) -> tuple[list[EmailLog], int]:
    """Retrieve a paginated slice of email delivery logs for a campaign.

    Logs are joined through recipients so only attempts belonging to the
    campaign are returned, ordered newest-first.

    Args:
        db: Active SQLAlchemy database session.
        campaign_id: Target campaign UUID.
        page: 1-indexed page number.
        page_size: Number of records per page.
        status_filter: Optional delivery status filter string.

    Returns:
        Tuple containing (list of EmailLog objects for the page, total count).
    """
    conditions = [Recipient.campaign_id == campaign_id]
    if status_filter:
        conditions.append(EmailLog.status == status_filter)
    total = db.scalar(
        select(func.count(EmailLog.id)).join(Recipient, EmailLog.recipient_id == Recipient.id).where(*conditions)
    ) or 0
    query = (
        select(EmailLog)
        .join(Recipient, EmailLog.recipient_id == Recipient.id)
        .where(*conditions)
        .order_by(EmailLog.timestamp.desc(), EmailLog.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return list(db.scalars(query).all()), total


def is_valid_campaign_id(val: str) -> bool:
    """Validate whether a string is a valid UUID representation.

    Args:
        val: Input string to validate.

    Returns:
        True if valid UUID, False otherwise.
    """
    try:
        uuid.UUID(val)
        return True
    except (ValueError, AttributeError, TypeError):
        return False


def format_campaign_summary(campaign: Campaign) -> str:
    """Format a human-readable summary string for a campaign.

    Args:
        campaign: Target Campaign object.

    Returns:
        Formatted summary string describing subject and status.
    """
    status_str = campaign.status.value if isinstance(campaign.status, CampaignStatus) else str(campaign.status)
    return f"Campaign '{campaign.subject}' [{status_str}] - Total: {campaign.total_emails}, Sent: {campaign.sent_count}, Failed: {campaign.failed_count}"


def aggregate_campaign_stats(db: Session) -> dict[str, int]:
    """Compute aggregate delivery statistics across all campaigns.

    Args:
        db: Active SQLAlchemy database session.

    Returns:
        Dictionary with total campaign count and summed sent/failed email totals.
    """
    total_campaigns = db.scalar(select(func.count(Campaign.id))) or 0
    total_sent = db.scalar(select(func.coalesce(func.sum(Campaign.sent_count), 0))) or 0
    total_failed = db.scalar(select(func.coalesce(func.sum(Campaign.failed_count), 0))) or 0
    return {
        "total_campaigns": total_campaigns,
        "total_emails_sent": total_sent,
        "total_emails_failed": total_failed,
    }



