"""Pydantic schemas for campaign APIs."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class CampaignCreate(BaseModel):
    subject: str = Field(..., min_length=1, max_length=200)
    message: str = Field(..., min_length=1, max_length=10000)


class CampaignResponse(BaseModel):
    id: UUID
    subject: str
    message: str
    total_emails: int
    sent_count: int
    failed_count: int
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class CampaignListResponse(BaseModel):
    items: list[CampaignResponse]
    page: int
    page_size: int
    total: int


class CampaignStatusResponse(BaseModel):
    campaign_id: UUID
    status: str
    total_emails: int
    sent_count: int
    failed_count: int
    pending_count: int
    progress_percent: float
    last_error: str | None = None
