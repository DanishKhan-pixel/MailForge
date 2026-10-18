"""Common API response schemas and query parameters."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class MessageResponse(BaseModel):
    """Generic status message response schema."""

    message: str = Field(..., description="Summary status message")


class PaginationParams(BaseModel):
    """Pagination query parameter validation model."""

    page: int = Field(default=1, ge=1, description="1-indexed page number")
    page_size: int = Field(default=10, ge=1, le=100, description="Number of items per page")

    @property
    def offset(self) -> int:
        """Calculate SQL database query offset based on page and page size."""
        return (self.page - 1) * self.page_size


class PaginationMeta(BaseModel):
    """Pagination metadata model for paginated API list responses."""

    page: int = Field(..., ge=1, description="Current 1-indexed page number")
    page_size: int = Field(..., ge=1, description="Number of items per page")
    total_items: int = Field(..., ge=0, description="Total number of matching records")
    total_pages: int = Field(..., ge=0, description="Total number of pages")
    has_next: bool = Field(default=False, description="Whether a next page exists")
    has_previous: bool = Field(default=False, description="Whether a previous page exists")

    @classmethod
    def from_counts(cls, page: int, page_size: int, total_items: int) -> PaginationMeta:
        """Construct PaginationMeta automatically from page, page_size, and total count."""
        import math

        total_pages = math.ceil(total_items / page_size) if total_items > 0 else 0
        return cls(
            page=page,
            page_size=page_size,
            total_items=total_items,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_previous=page > 1 and total_pages > 0,
        )


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


class ApiStatusResponse(BaseModel):
    """System overview runtime status response schema."""

    app_name: str = Field(..., description="Application service name")
    version: str = Field(..., description="Application semantic version")
    environment: str = Field(..., description="Active runtime environment")


class SystemInfoResponse(BaseModel):
    """Detailed environment and infrastructure telemetry response schema."""

    app_name: str = Field(..., description="Application service name")
    version: str = Field(..., description="Application semantic version")
    environment: str = Field(..., description="Active runtime environment")
    debug: bool = Field(default=False, description="Debug mode indicator")
    testing: bool = Field(default=False, description="Testing mode indicator")


class BulkDeleteResponse(BaseModel):
    """Batch deletion response schema containing deleted count."""

    deleted_count: int = Field(..., ge=0, description="Count of successfully removed records")
    message: str = Field(default="Records deleted successfully", description="Summary status message")


class BatchOperationResult(BaseModel):
    """Generic status result model for bulk batch operations."""

    total_processed: int = Field(..., ge=0, description="Total count of items processed")
    success_count: int = Field(..., ge=0, description="Count of successfully processed items")
    failure_count: int = Field(default=0, ge=0, description="Count of failed items")


class FilterParams(BaseModel):
    """Generic search and status filter query parameter validation model."""

    status: str | None = Field(default=None, description="Optional status filter string")
    search: str | None = Field(default=None, max_length=100, description="Optional search term string")


class DateRangeFilter(BaseModel):
    """Query filter parameters for filtering records by created timestamp range."""

    start_date: datetime | None = Field(default=None, description="Optional start datetime boundary")
    end_date: datetime | None = Field(default=None, description="Optional end datetime boundary")


class SortParams(BaseModel):
    """Query parameter model for column sorting configuration."""

    sort_by: str = Field(default="created_at", description="Field name to sort results by")
    order: str = Field(default="desc", pattern="^(asc|desc)$", description="Sort ordering direction (asc or desc)")

