"""Schemas for recipients and sending requests."""

from __future__ import annotations

from pydantic import BaseModel, Field


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

