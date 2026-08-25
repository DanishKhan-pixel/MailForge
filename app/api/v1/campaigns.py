"""Campaign API routes."""

from __future__ import annotations

import logging
import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, File, Query, UploadFile
from sqlalchemy.orm import Session

from app.core.rate_limit import rate_limit
from app.db.session import get_db
from app.schemas.campaign import (
    CampaignCreate,
    CampaignListResponse,
    CampaignResponse,
    CampaignStatusResponse,
)
from app.schemas.recipient import SendOptions, SendTriggerResponse, UploadResponse
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
from app.workers.tasks import send_campaign_emails

router = APIRouter(prefix="/campaigns", tags=["Campaigns"])
logger = logging.getLogger(__name__)


@router.post("", response_model=CampaignResponse, dependencies=[Depends(rate_limit(20, 60))])
def create_campaign_endpoint(payload: CampaignCreate, db: Session = Depends(get_db)) -> CampaignResponse:
    campaign = create_campaign(db, payload.subject, payload.message)
    return CampaignResponse.model_validate(campaign)


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
    status: str | None = Query(None),
    db: Session = Depends(get_db),
) -> CampaignListResponse:
    items, total = list_campaigns(db, page, page_size, status)
    return CampaignListResponse(
        items=[CampaignResponse.model_validate(item) for item in items],
        page=page,
        page_size=page_size,
        total=total,
    )


@router.get("/{campaign_id}", response_model=CampaignResponse, dependencies=[Depends(rate_limit(60, 60))])
def get_campaign(campaign_id: uuid.UUID, db: Session = Depends(get_db)) -> CampaignResponse:
    campaign = get_campaign_or_404(db, campaign_id)
    return CampaignResponse.model_validate(campaign)


@router.get(
    "/{campaign_id}/status",
    response_model=CampaignStatusResponse,
    dependencies=[Depends(rate_limit(120, 60))],
)
def get_campaign_status(campaign_id: uuid.UUID, db: Session = Depends(get_db)) -> CampaignStatusResponse:
    campaign = get_campaign_or_404(db, campaign_id)
    payload = campaign_status_payload(campaign, latest_campaign_error(db, campaign_id))
    return CampaignStatusResponse(**payload)



def getattr():
    
