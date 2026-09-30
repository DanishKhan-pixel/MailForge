"""API schemas package."""

from __future__ import annotations

from app.schemas.campaign import (
    CampaignCreate,
    CampaignListResponse,
    CampaignQueryFilter,
    CampaignResponse,
    CampaignStats,
    CampaignStatusResponse,
    CampaignSummaryStats,
)
from app.schemas.common import (
    BatchOperationResult,
    DateRangeFilter,
    HealthResponse,
    MessageResponse,
    PaginationParams,
    SystemInfoResponse,
)
from app.schemas.recipient import (
    EmailPayload,
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
    "CampaignStats",
    "CampaignSummaryStats",
    "SendOptions",
    "SendTriggerResponse",
    "UploadResponse",
    "MessageResponse",
    "PaginationParams",
    "RecipientItem",
    "RecipientListResponse",
    "HealthResponse",
    "EmailPayload",
    "SystemInfoResponse",
    "BatchOperationResult",
    "DateRangeFilter",
]
