"""Schemas for recipients and sending requests."""

from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field


class SendTriggerResponse(BaseModel):
    """Response returned when triggering campaign execution."""

    message: str = Field(..., description="Status summary message")
    task_id: str | None = Field(default=None, description="Celery task ID if scheduled via Celery worker")


class UploadResponse(BaseModel):
    """Response returned upon successful recipient CSV upload."""

    message: str = Field(..., description="Status summary message")
    recipient_count: int = Field(..., description="Number of unique valid recipients uploaded")


class SendOptions(BaseModel):
    """Execution options when initiating campaign send task."""

    delay_seconds: int = Field(default=4, ge=3, le=5, description="Delay between email dispatches in seconds")


class RecipientItem(BaseModel):
    """Schema representing an individual email campaign recipient."""

    email: EmailStr = Field(..., description="Recipient email address")
    name: str | None = Field(default=None, description="Optional recipient display name")


class RecipientListResponse(BaseModel):
    """Paginated list response of recipients belonging to a campaign."""

    items: list[RecipientItem] = Field(..., description="List of recipient records")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Page size limit")
    total: int = Field(..., description="Total count of recipients")


class EmailPayload(BaseModel):
    """Payload representing an individual outbound email dispatch."""

    recipient: EmailStr = Field(..., description="Target recipient email address")
    subject: str = Field(..., min_length=1, max_length=200, description="Email subject line")
    body: str = Field(..., min_length=1, max_length=10000, description="Email body message text")



