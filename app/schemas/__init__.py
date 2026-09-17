"""API schemas package."""

from __future__ import annotations

from app.schemas.campaign import (
    CampaignCreate,
    CampaignListResponse,
    CampaignQueryFilter,
    CampaignResponse,
    CampaignStatusResponse,
)
from app.schemas.common import HealthResponse, MessageResponse, PaginationParams
from app.schemas.recipient import (
    RecipientItem,
    RecipientListResponse,
    SendOptions,
    SendTriggerResponse,
    UploadResponse,
)

__all__ = [
    "CampaignCreate",
    "CampaignResponse",
    "CampaignListResponse",
    "CampaignStatusResponse",
    "CampaignQueryFilter",
    "SendOptions",
    "SendTriggerResponse",
    "UploadResponse",
    "MessageResponse",
    "PaginationParams",
    "RecipientItem",
    "RecipientListResponse",
    "HealthResponse",
]
