"""API schemas package."""

from __future__ import annotations

from app.schemas.campaign import (
    CampaignCreate,
    CampaignListResponse,
    CampaignResponse,
    CampaignStatusResponse,
)
from app.schemas.common import MessageResponse
from app.schemas.recipient import SendOptions, SendTriggerResponse, UploadResponse

__all__ = [
    "CampaignCreate",
    "CampaignResponse",
    "CampaignListResponse",
    "CampaignStatusResponse",
    "SendOptions",
    "SendTriggerResponse",
    "UploadResponse",
    "MessageResponse",
]
