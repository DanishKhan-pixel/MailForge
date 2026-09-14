"""API integration tests for public endpoints and health checks."""

from __future__ import annotations

import uuid
from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from app.db.session import get_db
from app.main import app
from app.schemas.recipient import RecipientItem

client = TestClient(app)


def test_health_check_endpoint() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_root_index_endpoint() -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_dashboard_endpoint() -> None:
    response = client.get("/dashboard")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_list_campaign_recipients_endpoint() -> None:
    cid = uuid.uuid4()
    db = MagicMock()
    db.get.return_value = MagicMock()
    db.scalars.return_value.all.return_value = [
        RecipientItem(email="alice@example.com", name="Alice"),
        RecipientItem(email="bob@example.com", name="Bob"),
    ]
    app.dependency_overrides[get_db] = lambda: db
    try:
        response = client.get(f"/campaigns/{cid}/recipients")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 2
    assert payload["items"] == [
        {"email": "alice@example.com", "name": "Alice"},
        {"email": "bob@example.com", "name": "Bob"},
    ]


def test_list_campaign_recipients_missing_campaign_returns_404() -> None:
    cid = uuid.uuid4()
    db = MagicMock()
    db.get.return_value = None
    app.dependency_overrides[get_db] = lambda: db
    try:
        response = client.get(f"/campaigns/{cid}/recipients")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404
