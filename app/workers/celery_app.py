"""Celery application factory."""

from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "mailforge_worker",
    broker=settings.redis_url,
    backend=settings.celery_result_backend,
)

celery_app.conf.update(
    task_track_started=True,
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
)
