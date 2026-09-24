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


class HealthResponse(BaseModel):
    """System health status response schema."""

    status: str = Field(default="ok", description="Service health indicator")


class ReadyResponse(BaseModel):
    """Readiness probe response schema."""

    status: str = Field(default="ready", description="Readiness indicator")


class ErrorDetail(BaseModel):
    """Detailed API error message model."""

    detail: str = Field(..., description="Error message details describing the failure")
    code: str | None = Field(default=None, description="Optional error code indicator")
