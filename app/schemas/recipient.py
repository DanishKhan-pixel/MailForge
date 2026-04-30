"""Schemas for recipients and sending requests."""

from pydantic import BaseModel, Field


class SendTriggerResponse(BaseModel):
    message: str
    task_id: str | None = None


class UploadResponse(BaseModel):
    message: str
    recipient_count: int


class SendOptions(BaseModel):
    delay_seconds: int = Field(default=4, ge=3, le=5)
