"""Common API response schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field


class MessageResponse(BaseModel):
    """Generic status message response schema."""

    message: str = Field(..., description="Summary status message")

