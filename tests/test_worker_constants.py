"""Unit tests for Celery worker status constants."""

from __future__ import annotations

from app.workers.constants import (
    TASK_STATUS_COMPLETED,
    TASK_STATUS_FAILED,
    TASK_STATUS_MISSING_CAMPAIGN,
)


def test_worker_status_constants() -> None:
    assert TASK_STATUS_COMPLETED == "completed"
    assert TASK_STATUS_MISSING_CAMPAIGN == "missing_campaign"
    assert TASK_STATUS_FAILED == "failed"
