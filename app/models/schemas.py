"""Pydantic models used for API request/response validation."""

from pydantic import BaseModel, Field


class SendEmailRequest(BaseModel):
    """Request payload for triggering email sends."""

    subject: str = Field(..., min_length=1, max_length=200, description="Email subject")
    message: str = Field(
        ...,
        min_length=1,
        max_length=10000,
        description="Email body with optional placeholders like {name}",
    )
    delay_seconds: int = Field(
        default=4,
        ge=3,
        le=5,
        description="Delay between emails to reduce spam detection risk.",
    )


class StatusResponse(BaseModel):
    """Progress snapshot for an email sending job."""

    is_running: bool
    total: int
    success_count: int
    failed_count: int
    last_error: str | None
