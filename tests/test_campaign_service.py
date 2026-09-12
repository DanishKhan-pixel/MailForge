"""Unit tests for campaign service business logic."""

from __future__ import annotations

import uuid
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from app.db.models import Campaign, CampaignStatus
from app.services.campaign_service import campaign_status_payload, ensure_can_send


def test_campaign_status_payload_calculation() -> None:
    campaign = MagicMock(spec=Campaign)
    campaign.id = uuid.uuid4()
    campaign.status = CampaignStatus.running
    campaign.total_emails = 100
    campaign.sent_count = 40
    campaign.failed_count = 10

    payload = campaign_status_payload(campaign, last_error="Connection error")
    assert payload["campaign_id"] == campaign.id
    assert payload["status"] == "running"
    assert payload["total_emails"] == 100
    assert payload["sent_count"] == 40
    assert payload["failed_count"] == 10
    assert payload["pending_count"] == 50
    assert payload["progress_percent"] == 50.0
    assert payload["last_error"] == "Connection error"


def test_ensure_can_send_zero_recipients() -> None:
    campaign = MagicMock(spec=Campaign)
    campaign.total_emails = 0
    campaign.status = CampaignStatus.pending

    with pytest.raises(HTTPException) as exc_info:
        ensure_can_send(campaign)
    assert exc_info.value.status_code == 400
    assert "Upload recipients" in exc_info.value.detail


def test_ensure_can_send_already_running() -> None:
    campaign = MagicMock(spec=Campaign)
    campaign.total_emails = 50
    campaign.status = CampaignStatus.running

    with pytest.raises(HTTPException) as exc_info:
        ensure_can_send(campaign)
    assert exc_info.value.status_code == 409
    assert "already running" in exc_info.value.detail


def test_ensure_can_send_valid() -> None:
    campaign = MagicMock(spec=Campaign)
    campaign.total_emails = 50
    campaign.status = CampaignStatus.pending

    # Should not raise any exception
    ensure_can_send(campaign)


def test_get_campaign_recipients_query() -> None:
    from app.services.campaign_service import get_campaign_recipients

    db = MagicMock()
    cid = uuid.uuid4()
    mock_recipient = MagicMock()
    db.scalars.return_value.all.return_value = [mock_recipient]

    result = get_campaign_recipients(db, cid)
    assert len(result) == 1
    assert result[0] == mock_recipient


