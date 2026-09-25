"""Campaign API routes."""

from __future__ import annotations

import logging
import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core.rate_limit import rate_limit
from app.db.models import CampaignStatus, RecipientStatus
from app.db.session import get_db
from app.schemas.campaign import (
    CampaignCreate,
    CampaignListResponse,
    CampaignResponse,
    CampaignStats,
    CampaignStatusResponse,
    CampaignUpdate,
    EmailLogItem,
    EmailLogListResponse,
)
from app.schemas.recipient import (
    RecipientDetail,
    RecipientItem,
    RecipientListResponse,
    RecipientRetryResponse,
    SendOptions,
    SendTriggerResponse,
    UploadResponse,
)
from app.services.campaign_service import (
    aggregate_campaign_stats,
    build_recipients_csv,
    campaign_status_payload,
    create_campaign,
    delete_campaign,
    delete_campaign_recipient,
    ensure_can_send,
    get_campaign_or_404,
    get_campaign_recipient_or_404,
    get_campaign_recipients,
    latest_campaign_error,
    list_campaigns,
    mark_campaign_running,
    paginate_campaign_logs,
    paginate_campaign_recipients,
    retry_failed_recipients,
    update_campaign,
    upload_recipients,
)
from app.services.csv_service import parse_recipients_csv
from app.workers.tasks import send_campaign_emails

router = APIRouter(prefix="/campaigns", tags=["Campaigns"])
logger = logging.getLogger(__name__)


@router.post("", response_model=CampaignResponse, dependencies=[Depends(rate_limit(20, 60))])
def create_campaign_endpoint(payload: CampaignCreate, db: Session = Depends(get_db)) -> CampaignResponse:
    """Create a new email campaign with a subject line and template message."""
    campaign = create_campaign(db, payload.subject, payload.message)
    return CampaignResponse.model_validate(campaign)


@router.patch("/{campaign_id}", response_model=CampaignResponse, dependencies=[Depends(rate_limit(20, 60))])
def update_campaign_endpoint(
    campaign_id: uuid.UUID,
    payload: CampaignUpdate,
    db: Session = Depends(get_db),
) -> CampaignResponse:
    """Update the subject or message of an existing campaign."""
    campaign = get_campaign_or_404(db, campaign_id)
    if campaign.status == CampaignStatus.running:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot update campaign while it is running.",
        )
    updated = update_campaign(db, campaign, subject=payload.subject, message=payload.message)
    return CampaignResponse.model_validate(updated)


@router.post(
    "/{campaign_id}/upload",
    response_model=UploadResponse,
    dependencies=[Depends(rate_limit(20, 60))],
)
async def upload_campaign_csv(
    campaign_id: uuid.UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> UploadResponse:
    """Upload and parse recipient list CSV file for a specific campaign."""
    campaign = get_campaign_or_404(db, campaign_id)
    rows = await parse_recipients_csv(file)
    count = upload_recipients(db, campaign, rows)
    return UploadResponse(message="CSV uploaded successfully.", recipient_count=count)


@router.post(
    "/{campaign_id}/send",
    response_model=SendTriggerResponse,
    dependencies=[Depends(rate_limit(10, 60))],
)
def send_campaign(
    campaign_id: uuid.UUID,
    payload: SendOptions,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> SendTriggerResponse:
    """Trigger background email sending task via Celery worker with fallback mode."""
    campaign = get_campaign_or_404(db, campaign_id)
    ensure_can_send(campaign)
    mark_campaign_running(db, campaign)
    try:
        task = send_campaign_emails.delay(str(campaign_id), payload.delay_seconds)
        return SendTriggerResponse(message="Campaign sending started.", task_id=task.id)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Celery unavailable, falling back to FastAPI BackgroundTasks: %s", str(exc))
        background_tasks.add_task(send_campaign_emails.run, str(campaign_id), payload.delay_seconds)
        return SendTriggerResponse(message="Campaign sending started (fallback mode).", task_id=None)


@router.get("", response_model=CampaignListResponse, dependencies=[Depends(rate_limit(60, 60))])
def list_campaigns_endpoint(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    status: CampaignStatus | None = Query(None),
    db: Session = Depends(get_db),
) -> CampaignListResponse:
    """List all created email campaigns with status filtering and pagination support."""
    status_filter = status.value if status else None
    items, total = list_campaigns(db, page, page_size, status_filter)
    return CampaignListResponse(
        items=[CampaignResponse.model_validate(item) for item in items],
        page=page,
        page_size=page_size,
        total=total,
    )


@router.get("/stats", response_model=CampaignStats, dependencies=[Depends(rate_limit(60, 60))])
def campaign_stats_endpoint(db: Session = Depends(get_db)) -> CampaignStats:
    """Return aggregate delivery statistics across all campaigns."""
    return CampaignStats(**aggregate_campaign_stats(db))


@router.get("/{campaign_id}", response_model=CampaignResponse, dependencies=[Depends(rate_limit(60, 60))])
def get_campaign(campaign_id: uuid.UUID, db: Session = Depends(get_db)) -> CampaignResponse:
    """Retrieve details and delivery metrics for a specific campaign by ID."""
    campaign = get_campaign_or_404(db, campaign_id)
    return CampaignResponse.model_validate(campaign)


@router.get(
    "/{campaign_id}/status",
    response_model=CampaignStatusResponse,
    dependencies=[Depends(rate_limit(120, 60))],
)
def get_campaign_status(campaign_id: uuid.UUID, db: Session = Depends(get_db)) -> CampaignStatusResponse:
    """Retrieve real-time execution status, progress percentage, and errors for a campaign."""
    campaign = get_campaign_or_404(db, campaign_id)
    payload = campaign_status_payload(campaign, latest_campaign_error(db, campaign_id))
    return CampaignStatusResponse(**payload)


@router.delete(
    "/{campaign_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(rate_limit(20, 60))],
)
def delete_campaign_endpoint(campaign_id: uuid.UUID, db: Session = Depends(get_db)) -> None:
    """Delete a campaign along with its recipients and email logs."""
    campaign = get_campaign_or_404(db, campaign_id)
    delete_campaign(db, campaign)


@router.get(
    "/{campaign_id}/recipients",
    response_model=RecipientListResponse,
    dependencies=[Depends(rate_limit(60, 60))],
)
def list_campaign_recipients(
    campaign_id: uuid.UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: RecipientStatus | None = Query(None),
    db: Session = Depends(get_db),
) -> RecipientListResponse:
    """List paginated recipient records registered for a specific campaign."""
    get_campaign_or_404(db, campaign_id)
    recipients, total = paginate_campaign_recipients(
        db, campaign_id, page, page_size, status.value if status else None
    )
    return RecipientListResponse(
        items=[RecipientItem(email=recipient.email, name=recipient.name) for recipient in recipients],
        page=page,
        page_size=page_size,
        total=total,
    )


@router.get(
    "/{campaign_id}/recipients/export",
    response_class=Response,
    dependencies=[Depends(rate_limit(10, 60))],
)
def export_campaign_recipients(
    campaign_id: uuid.UUID,
    status: RecipientStatus | None = Query(None),
    db: Session = Depends(get_db),
) -> Response:
    """Download the recipient list for a campaign as a CSV file."""
    campaign = get_campaign_or_404(db, campaign_id)
    recipients = get_campaign_recipients(db, campaign_id, status.value if status else None)
    csv_content = build_recipients_csv(recipients)
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="campaign_{campaign.id}_recipients.csv"',
        },
    )


@router.get(
    "/{campaign_id}/recipients/{recipient_id}",
    response_model=RecipientDetail,
    dependencies=[Depends(rate_limit(60, 60))],
)
def get_campaign_recipient(
    campaign_id: uuid.UUID,
    recipient_id: int,
    db: Session = Depends(get_db),
) -> RecipientDetail:
    """Retrieve detailed delivery information for a single campaign recipient."""
    get_campaign_or_404(db, campaign_id)
    recipient = get_campaign_recipient_or_404(db, campaign_id, recipient_id)
    status_value = (
        recipient.status.value if isinstance(recipient.status, RecipientStatus) else str(recipient.status)
    )
    return RecipientDetail(
        id=recipient.id,
        email=recipient.email,
        name=recipient.name,
        status=status_value,
        error_message=recipient.error_message,
        sent_at=recipient.sent_at,
    )


@router.delete(
    "/{campaign_id}/recipients/{recipient_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(rate_limit(20, 60))],
)
def delete_campaign_recipient_endpoint(
    campaign_id: uuid.UUID,
    recipient_id: int,
    db: Session = Depends(get_db),
) -> None:
    """Delete a single recipient from a campaign and reconcile counters."""
    campaign = get_campaign_or_404(db, campaign_id)
    recipient = get_campaign_recipient_or_404(db, campaign_id, recipient_id)
    delete_campaign_recipient(db, campaign, recipient)


@router.post(
    "/{campaign_id}/recipients/retry",
    response_model=RecipientRetryResponse,
    dependencies=[Depends(rate_limit(10, 60))],
)
def retry_failed_recipients_endpoint(
    campaign_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> RecipientRetryResponse:
    """Reset failed recipients of a campaign back to pending for a retry attempt."""
    campaign = get_campaign_or_404(db, campaign_id)
    ensure_can_send(campaign)
    count = retry_failed_recipients(db, campaign)
    return RecipientRetryResponse(message="Failed recipients queued for retry.", recipient_count=count)


@router.get(
    "/{campaign_id}/logs",
    response_model=EmailLogListResponse,
    dependencies=[Depends(rate_limit(60, 60))],
)
def list_campaign_logs(
    campaign_id: uuid.UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> EmailLogListResponse:
    """List paginated email delivery log records for a specific campaign."""
    get_campaign_or_404(db, campaign_id)
    logs, total = paginate_campaign_logs(db, campaign_id, page, page_size)
    return EmailLogListResponse(
        items=[
            EmailLogItem(
                id=log.id,
                recipient_id=log.recipient_id,
                recipient_email=log.recipient.email,
                status=log.status,
                response=log.response,
                timestamp=log.timestamp,
            )
            for log in logs
        ],
        page=page,
        page_size=page_size,
        total=total,
    )


