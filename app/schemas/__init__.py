"""API schemas package."""

from __future__ import annotations

from app.schemas.campaign import (
    CampaignCreate,
    CampaignListResponse,
    CampaignResponse,
    CampaignStatusResponse,
)
from app.schemas.common import MessageResponse, PaginationParams
from app.schemas.recipient import RecipientItem, SendOptions, SendTriggerResponse, UploadResponse

__all__ = [
    "CampaignCreate",
    "CampaignResponse",
    "CampaignListResponse",
    "CampaignStatusResponse",
    "SendOptions",
    "SendTriggerResponse",
    "UploadResponse",
    "MessageResponse",
    "PaginationParams",
    "RecipientItem",
]
