"""API integration tests for public endpoints and health checks."""

from __future__ import annotations

import uuid
from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from app.db.session import get_db
from app.main import app
from app.schemas.recipient import RecipientItem
from app.db.models import RecipientStatus

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


def test_campaign_stats_endpoint() -> None:
    db = MagicMock()
    db.scalar.side_effect = [4, 320, 12]
    app.dependency_overrides[get_db] = lambda: db
    try:
        response = client.get("/campaigns/stats")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {"total_campaigns": 4, "total_emails_sent": 320, "total_emails_failed": 12}


def test_delete_campaign_endpoint_returns_204() -> None:
    cid = uuid.uuid4()
    campaign = MagicMock()
    db = MagicMock()
    db.get.return_value = campaign
    app.dependency_overrides[get_db] = lambda: db
    try:
        response = client.delete(f"/campaigns/{cid}")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 204
    db.delete.assert_called_once_with(campaign)
    db.commit.assert_called_once()


def test_delete_campaign_endpoint_missing_returns_404() -> None:
    cid = uuid.uuid4()
    db = MagicMock()
    db.get.return_value = None
    app.dependency_overrides[get_db] = lambda: db
    try:
        response = client.delete(f"/campaigns/{cid}")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404


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


def test_list_campaign_recipients_accepts_status_filter() -> None:
    cid = uuid.uuid4()
    db = MagicMock()
    db.get.return_value = MagicMock()
    db.scalar.return_value = 1
    db.scalars.return_value.all.return_value = [
        RecipientItem(email="alice@example.com", name="Alice"),
    ]
    app.dependency_overrides[get_db] = lambda: db
    try:
        response = client.get(f"/campaigns/{cid}/recipients?status=sent")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["total"] == 1


def test_list_campaign_recipients_rejects_invalid_status_filter() -> None:
    cid = uuid.uuid4()
    db = MagicMock()
    db.get.return_value = MagicMock()
    app.dependency_overrides[get_db] = lambda: db
    try:
        response = client.get(f"/campaigns/{cid}/recipients?status=bogus")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422


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


def test_export_campaign_recipients_endpoint() -> None:
    cid = uuid.uuid4()
    campaign = MagicMock()
    campaign.id = cid

    first = MagicMock()
    first.email = "alice@example.com"
    first.name = "Alice"
    first.status = RecipientStatus.sent
    second = MagicMock()
    second.email = "bob@example.com"
    second.name = None
    second.status = RecipientStatus.pending

    db = MagicMock()
    db.get.return_value = campaign
    db.scalars.return_value.all.return_value = [first, second]
    app.dependency_overrides[get_db] = lambda: db
    try:
        response = client.get(f"/campaigns/{cid}/recipients/export")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert 'attachment; filename="campaign_' in response.headers["content-disposition"]
    lines = response.text.strip().splitlines()
    assert lines[0] == "email,name,status"
    assert "alice@example.com,Alice,sent" in lines
    assert "bob@example.com,,pending" in lines


def test_export_campaign_recipients_missing_campaign_returns_404() -> None:
    cid = uuid.uuid4()
    db = MagicMock()
    db.get.return_value = None
    app.dependency_overrides[get_db] = lambda: db
    try:
        response = client.get(f"/campaigns/{cid}/recipients/export")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404


def test_send_campaign_endpoint_dispatches_via_celery(monkeypatch) -> None:
    from app.api.v1 import campaigns as campaigns_module
    from app.db.models import CampaignStatus

    cid = uuid.uuid4()
    campaign = MagicMock()
    campaign.id = cid
    campaign.total_emails = 5
    campaign.status = CampaignStatus.pending

    task = MagicMock()
    task.id = "celery-task-id"
    monkeypatch.setattr(campaigns_module.send_campaign_emails, "delay", MagicMock(return_value=task))

    db = MagicMock()
    db.get.return_value = campaign
    app.dependency_overrides[get_db] = lambda: db
    try:
        response = client.post(f"/campaigns/{cid}/send", json={"delay_seconds": 4})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["message"] == "Campaign sending started."
    assert payload["task_id"] == "celery-task-id"
    campaigns_module.send_campaign_emails.delay.assert_called_once_with(str(cid), 4)


def test_send_campaign_endpoint_falls_back_to_background_task(monkeypatch) -> None:
    from app.api.v1 import campaigns as campaigns_module
    from app.db.models import CampaignStatus

    cid = uuid.uuid4()
    campaign = MagicMock()
    campaign.id = cid
    campaign.total_emails = 3
    campaign.status = CampaignStatus.pending

    ran = []

    def _boom(*args, **kwargs):
        raise RuntimeError("Broker unreachable")

    def _run(*args, **kwargs):
        ran.append(args)

    monkeypatch.setattr(campaigns_module.send_campaign_emails, "delay", _boom)
    monkeypatch.setattr(campaigns_module.send_campaign_emails, "run", _run)

    db = MagicMock()
    db.get.return_value = campaign
    app.dependency_overrides[get_db] = lambda: db
    try:
        response = client.post(f"/campaigns/{cid}/send", json={"delay_seconds": 4})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["message"] == "Campaign sending started (fallback mode)."
    assert payload["task_id"] is None
    assert ran == [(str(cid), 4)]
