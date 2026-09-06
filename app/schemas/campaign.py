"""Pydantic schemas for campaign APIs."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class CampaignCreate(BaseModel):
    """Payload for creating a new campaign."""

    subject: str = Field(..., min_length=1, max_length=200, description="Email subject line")
    message: str = Field(..., min_length=1, max_length=10000, description="Email message template text")


class CampaignResponse(BaseModel):
    """Response structure for campaign data."""

    id: UUID = Field(..., description="Unique campaign identifier")
    subject: str = Field(..., description="Email subject line")
    message: str = Field(..., description="Email message template text")
    total_emails: int = Field(..., description="Total count of recipients in campaign")
    sent_count: int = Field(..., description="Count of successfully sent emails")
    failed_count: int = Field(..., description="Count of failed email deliveries")
    status: str = Field(..., description="Current status of campaign execution")
    created_at: datetime = Field(..., description="Timestamp when campaign was created")

    model_config = {"from_attributes": True}


class CampaignListResponse(BaseModel):
    """Paginated list response of campaigns."""

    items: list[CampaignResponse] = Field(..., description="List of campaign records")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Page size limit")
    total: int = Field(..., description="Total count of campaigns matching filter")


class CampaignStatusResponse(BaseModel):
    """Detailed progress telemetry response for a campaign."""

    campaign_id: UUID = Field(..., description="Unique campaign identifier")
    status: str = Field(..., description="Current campaign status")
    total_emails: int = Field(..., description="Total count of recipients")
    sent_count: int = Field(..., description="Count of sent emails")
    failed_count: int = Field(..., description="Count of failed emails")
    pending_count: int = Field(..., description="Count of pending emails remaining")
    progress_percent: float = Field(..., description="Percentage of emails processed (0-100)")
    last_error: str | None = Field(default=None, description="Most recent error message if any")

