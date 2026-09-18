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
    db.scalar.return_value = 2
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
    assert payload["page"] == 1
    assert payload["page_size"] == 20


def test_list_campaign_recipients_pagination() -> None:
    cid = uuid.uuid4()
    page_items = [RecipientItem(email=f"user{i}@example.com", name=f"User{i}") for i in range(10, 20)]
    db = MagicMock()
    db.get.return_value = MagicMock()
    db.scalar.return_value = 25
    db.scalars.return_value.all.return_value = page_items
    app.dependency_overrides[get_db] = lambda: db
    try:
        response = client.get(f"/campaigns/{cid}/recipients?page=2&page_size=10")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 25
    assert payload["page"] == 2
    assert payload["page_size"] == 10
    assert len(payload["items"]) == 10
    assert payload["items"][0]["email"] == "user10@example.com"


def test_list_campaign_recipients_page_out_of_range() -> None:
    cid = uuid.uuid4()
    db = MagicMock()
    db.get.return_value = MagicMock()
    db.scalar.return_value = 1
    db.scalars.return_value.all.return_value = []
    app.dependency_overrides[get_db] = lambda: db
    try:
        response = client.get(f"/campaigns/{cid}/recipients?page=5&page_size=20")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    assert payload["items"] == []
    assert payload["page"] == 5


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


def test_list_campaigns_accepts_valid_status_filter() -> None:
    db = MagicMock()
    db.scalars.return_value.all.return_value = []
    db.scalar.return_value = 0
    app.dependency_overrides[get_db] = lambda: db
    try:
        response = client.get("/campaigns?status=pending")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["items"] == []


def test_list_campaigns_rejects_invalid_status_filter() -> None:
    db = MagicMock()
    app.dependency_overrides[get_db] = lambda: db
    try:
        response = client.get("/campaigns?status=bogus")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422
