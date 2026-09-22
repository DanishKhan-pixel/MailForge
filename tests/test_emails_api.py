"""Unit tests for single-email dispatch API endpoint."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.core.rate_limit import reset_rate_limits
from app.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def _clear_rate_limits() -> None:
    reset_rate_limits()


def test_send_email_endpoint_success(monkeypatch) -> None:
    from app.api.v1 import emails

    sent = {}

    def _fake_send(recipient, subject, body) -> None:
        sent["recipient"] = recipient
        sent["subject"] = subject
        sent["body"] = body

    monkeypatch.setattr(emails.email_service, "send_email", _fake_send)

    response = client.post(
        "/emails",
        json={"recipient": "alice@example.com", "subject": "Welcome", "body": "Hi there"},
    )

    assert response.status_code == 200
    assert response.json() == {"message": "Email sent successfully."}
    assert sent == {"recipient": "alice@example.com", "subject": "Welcome", "body": "Hi there"}


def test_send_email_endpoint_rejects_invalid_recipient() -> None:
    response = client.post(
        "/emails",
        json={"recipient": "not-an-email", "subject": "Welcome", "body": "Hi there"},
    )

    assert response.status_code == 422


def test_send_email_endpoint_rejects_empty_body() -> None:
    response = client.post(
        "/emails",
        json={"recipient": "alice@example.com", "subject": "Welcome", "body": ""},
    )

    assert response.status_code == 422


def test_send_email_endpoint_rate_limited(monkeypatch) -> None:
    from app.api.v1 import emails

    counter = {"calls": 0}

    def _fake_send(recipient, subject, body) -> None:
        counter["calls"] += 1

    monkeypatch.setattr(emails.email_service, "send_email", _fake_send)
    payload = {"recipient": "alice@example.com", "subject": "Welcome", "body": "Hi"}

    responses = [client.post("/emails", json=payload).status_code for _ in range(21)]

    assert responses[0] == 200
    assert responses[-1] == 429
    assert counter["calls"] == 20


def test_send_email_endpoint_makes_smtp_call(monkeypatch) -> None:
    from app.services.email_service import EmailService

    service = EmailService()
    mock_send = MagicMock()
    monkeypatch.setattr(service, "send_email", mock_send)
    monkeypatch.setattr("app.api.v1.emails.email_service", service)

    response = client.post(
        "/emails",
        json={"recipient": "bob@example.com", "subject": "Hi", "body": "Hello"},
    )

    assert response.status_code == 200
    mock_send.assert_called_once_with("bob@example.com", "Hi", "Hello")