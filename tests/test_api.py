"""API integration tests for public endpoints and health checks."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.core.rate_limit import reset_rate_limits
from app.db.models import CampaignStatus, RecipientStatus
from app.db.session import get_db
from app.main import app
from app.schemas.recipient import RecipientItem

client = TestClient(app)


@pytest.fixture(autouse=True)
def _clear_rate_limits() -> None:
    reset_rate_limits()


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


def test_list_campaign_logs_endpoint() -> None:
    cid = uuid.uuid4()
    log = MagicMock()
    log.id = 44
    log.recipient_id = 7
    log.recipient.email = "alice@example.com"
    log.status = "sent"
    log.response = "SMTP delivered"
    log.timestamp = datetime(2026, 9, 1, 12, 0, tzinfo=timezone.utc)

    db = MagicMock()
    db.get.return_value = MagicMock()
    db.scalar.return_value = 25
    db.scalars.return_value.all.return_value = [log]
    app.dependency_overrides[get_db] = lambda: db
    try:
        response = client.get(f"/campaigns/{cid}/logs")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 25
    assert payload["page"] == 1
    assert payload["page_size"] == 20
    assert payload["items"] == [
        {
            "id": 44,
            "recipient_id": 7,
            "recipient_email": "alice@example.com",
            "status": "sent",
            "response": "SMTP delivered",
            "timestamp": "2026-09-01T12:00:00Z",
        }
    ]


def test_list_campaign_logs_empty_campaign() -> None:
    cid = uuid.uuid4()
    db = MagicMock()
    db.get.return_value = MagicMock()
    db.scalar.return_value = 0
    db.scalars.return_value.all.return_value = []
    app.dependency_overrides[get_db] = lambda: db
    try:
        response = client.get(f"/campaigns/{cid}/logs")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 0
    assert payload["items"] == []


def test_list_campaign_logs_missing_campaign_returns_404() -> None:
    cid = uuid.uuid4()
    db = MagicMock()
    db.get.return_value = None
    app.dependency_overrides[get_db] = lambda: db
    try:
        response = client.get(f"/campaigns/{cid}/logs")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404


def test_get_campaign_recipient_returns_details() -> None:
    cid = uuid.uuid4()
    recipient = MagicMock()
    recipient.id = 7
    recipient.campaign_id = cid
    recipient.email = "alice@example.com"
    recipient.name = "Alice"
    recipient.status = RecipientStatus.sent
    recipient.error_message = None
    recipient.sent_at = datetime(2026, 9, 1, 12, 0, tzinfo=timezone.utc)

    db = MagicMock()
    db.get.side_effect = [MagicMock(), recipient]
    app.dependency_overrides[get_db] = lambda: db
    try:
        response = client.get(f"/campaigns/{cid}/recipients/7")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "id": 7,
        "email": "alice@example.com",
        "name": "Alice",
        "status": "sent",
        "error_message": None,
        "sent_at": "2026-09-01T12:00:00Z",
    }


def test_get_campaign_recipient_missing_returns_404() -> None:
    cid = uuid.uuid4()
    db = MagicMock()
    db.get.side_effect = [MagicMock(), None]
    app.dependency_overrides[get_db] = lambda: db
    try:
        response = client.get(f"/campaigns/{cid}/recipients/7")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404


def test_get_campaign_recipient_wrong_campaign_returns_404() -> None:
    cid = uuid.uuid4()
    recipient = MagicMock()
    recipient.campaign_id = uuid.uuid4()
    db = MagicMock()
    db.get.side_effect = [MagicMock(), recipient]
    app.dependency_overrides[get_db] = lambda: db
    try:
        response = client.get(f"/campaigns/{cid}/recipients/7")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404


def test_retry_failed_recipients_endpoint() -> None:
    cid = uuid.uuid4()
    campaign = MagicMock()
    campaign.id = cid
    campaign.total_emails = 3
    campaign.status = CampaignStatus.pending

    db = MagicMock()
    db.get.return_value = campaign
    db.scalars.return_value.all.return_value = [MagicMock(), MagicMock()]
    app.dependency_overrides[get_db] = lambda: db
    try:
        response = client.post(f"/campaigns/{cid}/recipients/retry")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {"message": "Failed recipients queued for retry.", "recipient_count": 2}


def test_retry_failed_recipients_running_campaign_returns_409() -> None:
    cid = uuid.uuid4()
    campaign = MagicMock()
    campaign.id = cid
    campaign.total_emails = 3
    campaign.status = CampaignStatus.running

    db = MagicMock()
    db.get.return_value = campaign
    app.dependency_overrides[get_db] = lambda: db
    try:
        response = client.post(f"/campaigns/{cid}/recipients/retry")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 409


def test_retry_failed_recipients_missing_campaign_returns_404() -> None:
    cid = uuid.uuid4()
    db = MagicMock()
    db.get.return_value = None
    app.dependency_overrides[get_db] = lambda: db
    try:
        response = client.post(f"/campaigns/{cid}/recipients/retry")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404


def test_successful_response_includes_rate_limit_headers() -> None:
    from app.core.rate_limit import reset_rate_limits

    reset_rate_limits()
    db = MagicMock()
    db.scalars.return_value.all.return_value = []
    db.scalar.return_value = 0
    app.dependency_overrides[get_db] = lambda: db
    try:
        response = client.get("/campaigns")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.headers["X-RateLimit-Limit"] == "60"
    assert response.headers["X-RateLimit-Remaining"] == "59"
    assert int(response.headers["X-RateLimit-Reset"]) >= 0


def test_throttled_endpoint_returns_429_with_retry_after(monkeypatch) -> None:
    from app.api.v1 import emails as emails_module
    from app.core.rate_limit import reset_rate_limits

    reset_rate_limits()
    monkeypatch.setattr(emails_module.email_service, "send_email", lambda *args, **kwargs: None)

    payload = {"recipient": "alice@example.com", "subject": "Hi", "body": "Hello"}
    responses = [client.post("/emails", json=payload) for _ in range(21)]

    assert responses[0].status_code == 200
    assert responses[0].headers["X-RateLimit-Limit"] == "20"
    assert responses[-1].status_code == 429
    assert int(responses[-1].headers["Retry-After"]) >= 1


def test_update_campaign_endpoint_updates_subject_and_message() -> None:
    cid = uuid.uuid4()
    campaign = MagicMock()
    campaign.id = cid
    campaign.subject = "Old"
    campaign.message = "Old body"
    campaign.status = CampaignStatus.pending

    db = MagicMock()
    db.get.return_value = campaign
    app.dependency_overrides[get_db] = lambda: db
    try:
        response = client.patch(f"/campaigns/{cid}", json={"subject": "New", "message": "New body"})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert campaign.subject == "New"
    assert campaign.message == "New body"
    db.commit.assert_called_once()
    db.refresh.assert_called_once_with(campaign)


def test_update_campaign_endpoint_partial_update() -> None:
    cid = uuid.uuid4()
    campaign = MagicMock()
    campaign.id = cid
    campaign.subject = "Keep"
    campaign.message = "Old body"
    campaign.status = CampaignStatus.pending

    db = MagicMock()
    db.get.return_value = campaign
    app.dependency_overrides[get_db] = lambda: db
    try:
        response = client.patch(f"/campaigns/{cid}", json={"message": "New body"})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert campaign.subject == "Keep"
    assert campaign.message == "New body"


def test_update_campaign_endpoint_running_campaign_returns_409() -> None:
    cid = uuid.uuid4()
    campaign = MagicMock()
    campaign.id = cid
    campaign.status = CampaignStatus.running

    db = MagicMock()
    db.get.return_value = campaign
    app.dependency_overrides[get_db] = lambda: db
    try:
        response = client.patch(f"/campaigns/{cid}", json={"subject": "New"})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 409
    db.commit.assert_not_called()


def test_update_campaign_endpoint_missing_campaign_returns_404() -> None:
    cid = uuid.uuid4()
    db = MagicMock()
    db.get.return_value = None
    app.dependency_overrides[get_db] = lambda: db
    try:
        response = client.patch(f"/campaigns/{cid}", json={"subject": "New"})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404


def test_update_campaign_endpoint_sanitizes_line_break_subject() -> None:
    cid = uuid.uuid4()
    campaign = MagicMock()
    campaign.id = cid
    campaign.status = CampaignStatus.pending
    campaign.subject = "Old"
    campaign.message = "Body"

    db = MagicMock()
    db.get.return_value = campaign
    app.dependency_overrides[get_db] = lambda: db
    try:
        response = client.patch(f"/campaigns/{cid}", json={"subject": "Hello\nCC: evil@example.com"})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert campaign.subject == "Hello CC: evil@example.com"
    assert "\n" not in campaign.subject
    assert "\r" not in campaign.subject


def test_delete_campaign_recipient_endpoint_returns_204() -> None:
    cid = uuid.uuid4()
    campaign = MagicMock()
    campaign.id = cid
    campaign.total_emails = 10
    campaign.sent_count = 4
    campaign.failed_count = 1

    recipient = MagicMock()
    recipient.id = 7
    recipient.campaign_id = cid
    recipient.status = RecipientStatus.sent

    db = MagicMock()
    db.get.side_effect = [campaign, recipient]
    app.dependency_overrides[get_db] = lambda: db
    try:
        response = client.delete(f"/campaigns/{cid}/recipients/7")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 204
    db.delete.assert_called_once_with(recipient)
    db.commit.assert_called_once()
    assert campaign.total_emails == 9
    assert campaign.sent_count == 3


def test_delete_campaign_recipient_missing_recipient_returns_404() -> None:
    cid = uuid.uuid4()
    campaign = MagicMock()
    campaign.id = cid

    db = MagicMock()
    db.get.side_effect = [campaign, None]
    app.dependency_overrides[get_db] = lambda: db
    try:
        response = client.delete(f"/campaigns/{cid}/recipients/7")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404
    db.delete.assert_not_called()


def test_export_campaign_recipients_supports_status_filter() -> None:
    cid = uuid.uuid4()
    campaign = MagicMock()
    campaign.id = cid

    failed = MagicMock()
    failed.email = "bob@example.com"
    failed.name = None
    failed.status = RecipientStatus.failed

    db = MagicMock()
    db.get.return_value = campaign
    db.scalars.return_value.all.return_value = [failed]
    app.dependency_overrides[get_db] = lambda: db
    try:
        response = client.get(f"/campaigns/{cid}/recipients/export?status=failed")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    lines = response.text.strip().splitlines()
    assert lines[0] == "email,name,status"
    assert "bob@example.com,,failed" in lines
    assert len(lines) == 2


def test_export_campaign_recipients_rejects_invalid_status_filter() -> None:
    cid = uuid.uuid4()
    campaign = MagicMock()
    campaign.id = cid
    db = MagicMock()
    db.get.return_value = campaign
    app.dependency_overrides[get_db] = lambda: db
    try:
        response = client.get(f"/campaigns/{cid}/recipients/export?status=bogus")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422
