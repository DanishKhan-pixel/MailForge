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


def test_paginate_campaign_recipients_applies_db_pagination() -> None:
    from app.services.campaign_service import paginate_campaign_recipients

    db = MagicMock()
    db.scalar.return_value = 45
    db.scalars.return_value.all.return_value = [MagicMock(), MagicMock()]

    cid = uuid.uuid4()
    items, total = paginate_campaign_recipients(db, cid, page=2, page_size=10)

    assert total == 45
    assert len(items) == 2
    select_call = db.scalars.call_args.args[0]
    compiled = str(select_call.compile(compile_kwargs={"literal_binds": True}))
    assert "OFFSET" in compiled or "LIMIT" in compiled


def test_campaign_status_payload_truncates_long_last_error() -> None:
    long_error = "E" * 1000
    campaign = MagicMock(spec=Campaign)
    campaign.id = uuid.uuid4()
    campaign.status = CampaignStatus.completed
    campaign.total_emails = 10
    campaign.sent_count = 10
    campaign.failed_count = 0

    payload = campaign_status_payload(campaign, last_error=long_error)
    assert len(payload["last_error"]) == 500
    assert payload["last_error"].endswith("...")


def test_is_valid_campaign_id_validation() -> None:
    from app.services.campaign_service import is_valid_campaign_id

    valid_uuid_str = str(uuid.uuid4())
    assert is_valid_campaign_id(valid_uuid_str) is True
    assert is_valid_campaign_id("not-a-uuid") is False
    assert is_valid_campaign_id("") is False


def test_format_campaign_summary() -> None:
    from app.services.campaign_service import format_campaign_summary

    campaign = MagicMock(spec=Campaign)
    campaign.subject = "March Newsletter"
    campaign.status = CampaignStatus.pending
    campaign.total_emails = 50
    campaign.sent_count = 10
    campaign.failed_count = 2

    summary = format_campaign_summary(campaign)
    assert "March Newsletter" in summary
    assert "[pending]" in summary
    assert "Total: 50" in summary



