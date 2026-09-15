"""Unit tests for Celery application factory and runtime configuration."""

from __future__ import annotations

from app.core.config import settings
from app.workers.celery_app import celery_app


def test_celery_broker_and_backend_from_settings() -> None:
    assert celery_app.conf.broker_url == settings.redis_url
    assert celery_app.conf.result_backend == settings.celery_result_backend


def test_celery_task_serialization_is_json() -> None:
    assert celery_app.conf.task_serializer == "json"
    assert celery_app.conf.result_serializer == "json"
    assert "json" in celery_app.conf.accept_content


def test_celery_timezone_is_utc() -> None:
    assert celery_app.conf.timezone == "UTC"


def test_celery_task_tracking_enabled() -> None:
    assert celery_app.conf.task_track_started is True
