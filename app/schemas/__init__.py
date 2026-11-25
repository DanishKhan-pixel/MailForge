"""API schemas package."""

from __future__ import annotations

from app.schemas.campaign import (
    CampaignCreate,
    CampaignDuplicate,
    CampaignListResponse,
    CampaignQueryFilter,
    CampaignResponse,
    CampaignStats,
    CampaignStatusResponse,
    CampaignSummaryStats,
    EmailPreview,
)
from app.schemas.common import (
    BatchOperationResult,
    DateRangeFilter,
    HealthResponse,
    MessageResponse,
    PaginationMeta,
    PaginationParams,
    SortParams,
    SystemInfoResponse,
)
from app.schemas.recipient import (
    EmailPayload,
    RecipientBulkDelete,
    RecipientItem,
    RecipientListResponse,
    RecipientQueryFilter,
    RecipientSearchFilter,
    RecipientStats,
    RecipientUpdate,
    SendOptions,
    SendTriggerResponse,
    UploadResponse,
)

__all__ = [
    "CampaignCreate",
    "CampaignDuplicate",
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
    "PaginationMeta",
    "RecipientItem",
    "RecipientListResponse",
    "RecipientStats",
    "RecipientQueryFilter",
    "RecipientBulkDelete",
    "RecipientUpdate",
    "RecipientSearchFilter",
    "HealthResponse",
    "EmailPayload",
    "EmailPreview",
    "SystemInfoResponse",
    "BatchOperationResult",
    "DateRangeFilter",
    "SortParams",
]
