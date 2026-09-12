"""Unit tests for top-level package exports."""

from __future__ import annotations

import app.api
import app.api.v1
import app.core
import app.db
import app.schemas
import app.services
import app.utils
import app.workers


def test_core_package_exports() -> None:
    assert hasattr(app.core, "settings")
    assert hasattr(app.core, "configure_logging")
    assert hasattr(app.core, "rate_limit")


def test_db_package_exports() -> None:
    assert hasattr(app.db, "Base")
    assert hasattr(app.db, "SessionLocal")
    assert hasattr(app.db, "get_db")


def test_services_package_exports() -> None:
    assert hasattr(app.services, "create_campaign")
    assert hasattr(app.services, "parse_recipients_csv")
    assert hasattr(app.services, "EmailService")


def test_workers_package_exports() -> None:
    assert hasattr(app.workers, "celery_app")
    assert hasattr(app.workers, "send_campaign_emails")


def test_api_package_exports() -> None:
    assert hasattr(app.api, "campaigns_router")
    assert hasattr(app.api.v1, "campaigns_router")


def test_utils_package_exports() -> None:
    assert hasattr(app.utils, "mask_email")
    assert hasattr(app.utils, "format_utc_timestamp")
    assert hasattr(app.utils, "parse_iso_timestamp")
