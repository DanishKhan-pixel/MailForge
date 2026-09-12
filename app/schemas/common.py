"""Common API response schemas and query parameters."""

from __future__ import annotations

from pydantic import BaseModel, Field


class MessageResponse(BaseModel):
    """Generic status message response schema."""

    message: str = Field(..., description="Summary status message")


class PaginationParams(BaseModel):
    """Pagination query parameter validation model."""

    page: int = Field(default=1, ge=1, description="1-indexed page number")
    page_size: int = Field(default=10, ge=1, le=100, description="Number of items per page")
