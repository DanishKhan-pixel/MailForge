"""Unit tests for campaign service business logic."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from app.db.models import Campaign, CampaignStatus, EmailLog, Recipient, RecipientStatus
from app.services.campaign_service import (
    build_recipients_csv,
    campaign_status_payload,
    delete_campaign_recipient,
    ensure_can_send,
    paginate_campaign_logs,
    retry_failed_recipients,
)


def test_build_recipients_csv_serializes_rows() -> None:
    first = MagicMock(spec=RecipientStatus)
    first.email = "alice@example.com"
    first.name = "Alice"
    first.status = RecipientStatus.sent
    second = MagicMock(spec=RecipientStatus)
    second.email = "bob@example.com"
    second.name = None
    second.status = RecipientStatus.pending

    csv_text = build_recipients_csv([first, second])

    lines = csv_text.strip().splitlines()
    assert lines[0] == "email,name,status"
    assert "alice@example.com,Alice,sent" in lines
    assert "bob@example.com,,pending" in lines


def test_build_recipients_csv_handles_empty_list() -> None:
    assert build_recipients_csv([]).strip() == "email,name,status"


def test_paginate_campaign_logs_returns_ordered_slice() -> None:
    cid = uuid.uuid4()
    log = MagicMock(spec=EmailLog)
    log.id = 44
    log.recipient_id = 7
    log.status = "sent"
    log.response = "SMTP delivered"
    log.timestamp = datetime(2026, 9, 1, 12, 0, tzinfo=timezone.utc)

    db = MagicMock()
    db.scalar.return_value = 25
    db.scalars.return_value.all.return_value = [log]

    items, total = paginate_campaign_logs(db, cid, page=1, page_size=20)

    assert total == 25
    assert len(items) == 1
    assert items[0].id == 44
    assert items[0].status == "sent"


def test_paginate_campaign_logs_empty_campaign() -> None:
    cid = uuid.uuid4()
    db = MagicMock()
    db.scalar.return_value = 0
    db.scalars.return_value.all.return_value = []

    items, total = paginate_campaign_logs(db, cid, page=1, page_size=20)

    assert total == 0
    assert items == []


def test_paginate_campaign_logs_filters_by_status() -> None:
    cid = uuid.uuid4()
    db = MagicMock()
    db.scalar.return_value = 3
    db.scalars.return_value.all.return_value = [MagicMock()]

    items, total = paginate_campaign_logs(db, cid, page=1, page_size=20, status_filter="failed")

    assert total == 3
    assert len(items) == 1
    select_call = db.scalars.call_args.args[0]
    compiled = str(select_call.compile(compile_kwargs={"literal_binds": True}))
    assert "failed" in compiled


def test_retry_failed_recipients_resets_failed_rows() -> None:
    cid = uuid.uuid4()
    campaign = MagicMock(spec=Campaign)
    campaign.id = cid

    first = MagicMock(spec=Recipient)
    first.status = RecipientStatus.failed
    first.error_message = "Connection refused"
    first.sent_at = datetime(2026, 9, 1, 12, 0, tzinfo=timezone.utc)
    second = MagicMock(spec=Recipient)
    second.status = RecipientStatus.failed
    second.error_message = "Timeout"
    second.sent_at = datetime(2026, 9, 1, 13, 0, tzinfo=timezone.utc)

    db = MagicMock()
    db.scalars.return_value.all.return_value = [first, second]

    count = retry_failed_recipients(db, campaign)

    assert count == 2
    assert first.status == RecipientStatus.pending
    assert first.error_message is None
    assert first.sent_at is None
    assert second.status == RecipientStatus.pending
    db.commit.assert_called_once()


def test_retry_failed_recipients_noop_when_none_failed() -> None:
    campaign = MagicMock(spec=Campaign)
    campaign.id = uuid.uuid4()
    db = MagicMock()
    db.scalars.return_value.all.return_value = []

    assert retry_failed_recipients(db, campaign) == 0
    db.commit.assert_called_once()


def test_delete_campaign_recipient_decrements_sent_counter() -> None:
    campaign = MagicMock(spec=Campaign)
    campaign.total_emails = 10
    campaign.sent_count = 4
    campaign.failed_count = 1

    recipient = MagicMock(spec=Recipient)
    recipient.status = RecipientStatus.sent

    db = MagicMock()

    delete_campaign_recipient(db, campaign, recipient)

    db.delete.assert_called_once_with(recipient)
    db.commit.assert_called_once()
    assert campaign.total_emails == 9
    assert campaign.sent_count == 3
    assert campaign.failed_count == 1


def test_delete_campaign_recipient_decrements_failed_counter() -> None:
    campaign = MagicMock(spec=Campaign)
    campaign.total_emails = 5
    campaign.sent_count = 0
    campaign.failed_count = 2

    recipient = MagicMock(spec=Recipient)
    recipient.status = RecipientStatus.failed

    db = MagicMock()

    delete_campaign_recipient(db, campaign, recipient)

    assert campaign.total_emails == 4
    assert campaign.failed_count == 1
    assert campaign.sent_count == 0


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


def test_paginate_campaign_recipients_filters_by_status() -> None:
    from app.services.campaign_service import paginate_campaign_recipients

    db = MagicMock()
    db.scalar.return_value = 7
    db.scalars.return_value.all.return_value = [MagicMock()]

    cid = uuid.uuid4()
    items, total = paginate_campaign_recipients(db, cid, page=1, page_size=20, status_filter="sent")

    assert total == 7
    assert len(items) == 1
    select_call = db.scalars.call_args.args[0]
    compiled = str(select_call.compile(compile_kwargs={"literal_binds": True}))
    assert "status" in compiled
    assert "sent" in compiled


def test_paginate_campaign_recipients_searches_email_and_name() -> None:
    from app.services.campaign_service import paginate_campaign_recipients

    db = MagicMock()
    db.scalar.return_value = 3
    db.scalars.return_value.all.return_value = [MagicMock()]

    cid = uuid.uuid4()
    items, total = paginate_campaign_recipients(db, cid, page=1, page_size=20, search="ali")

    assert total == 3
    assert len(items) == 1
    select_call = db.scalars.call_args.args[0]
    compiled = str(select_call.compile(compile_kwargs={"literal_binds": True}))
    assert "LIKE" in compiled
    assert "%ali%" in compiled


def test_paginate_campaign_recipients_combines_search_and_status() -> None:
    from app.services.campaign_service import paginate_campaign_recipients

    db = MagicMock()
    db.scalar.return_value = 1
    db.scalars.return_value.all.return_value = [MagicMock()]

    cid = uuid.uuid4()
    items, total = paginate_campaign_recipients(db, cid, page=1, page_size=20, status_filter="sent", search="bo")

    assert total == 1
    select_call = db.scalars.call_args.args[0]
    compiled = str(select_call.compile(compile_kwargs={"literal_binds": True}))
    assert "sent" in compiled
    assert "%bo%" in compiled


def test_delete_campaign_removes_and_commits() -> None:
    from app.services.campaign_service import delete_campaign

    db = MagicMock()
    campaign = MagicMock(spec=Campaign)

    delete_campaign(db, campaign)

    db.delete.assert_called_once_with(campaign)
    db.commit.assert_called_once()


def test_aggregate_campaign_stats_sums_delivery_totals() -> None:
    from app.services.campaign_service import aggregate_campaign_stats

    db = MagicMock()
    db.scalar.side_effect = [3, 150, 5]

    stats = aggregate_campaign_stats(db)

    assert stats["total_campaigns"] == 3
    assert stats["total_emails_sent"] == 150
    assert stats["total_emails_failed"] == 5


def test_aggregate_campaign_stats_handles_empty_database() -> None:
    from app.services.campaign_service import aggregate_campaign_stats

    db = MagicMock()
    db.scalar.return_value = None

    stats = aggregate_campaign_stats(db)

    assert stats == {"total_campaigns": 0, "total_emails_sent": 0, "total_emails_failed": 0}


def test_upload_recipients_inserts_rows_in_chunks_and_updates_total() -> None:
    from app.services.campaign_service import RECIPIENT_UPLOAD_CHUNK_SIZE, upload_recipients

    rows = [{"email": f"user{i}@example.com", "name": f"User{i}"} for i in range(RECIPIENT_UPLOAD_CHUNK_SIZE + 10)]
    campaign = MagicMock(spec=Campaign)
    campaign.id = uuid.uuid4()
    campaign.total_emails = 0
    db = MagicMock()

    count = upload_recipients(db, campaign, rows)

    assert count == len(rows)
    assert campaign.total_emails == 0 + len(rows)
    assert db.add_all.call_count == 2
    assert db.flush.call_count == 2
    db.commit.assert_called_once()


def test_upload_recipients_single_chunk_for_small_batch() -> None:
    from app.services.campaign_service import upload_recipients

    rows = [{"email": "a@example.com", "name": "A"}, {"email": "b@example.com", "name": None}]
    campaign = MagicMock(spec=Campaign)
    campaign.id = uuid.uuid4()
    campaign.total_emails = 0
    db = MagicMock()

    count = upload_recipients(db, campaign, rows)

    assert count == 2
    assert db.add_all.call_count == 1
    assert db.flush.call_count == 1


def test_upload_recipients_skips_duplicate_emails_on_conflict() -> None:
    from sqlalchemy.exc import IntegrityError

    from app.services.campaign_service import upload_recipients

    rows = [{"email": "dup@example.com", "name": "D"}, {"email": "new@example.com", "name": "N"}]
    campaign = MagicMock(spec=Campaign)
    campaign.id = uuid.uuid4()
    campaign.total_emails = 5
    db = MagicMock()

    conflict = IntegrityError("INSERT", {}, Exception("duplicate key"))
    db.flush.side_effect = [conflict, None, conflict]

    count = upload_recipients(db, campaign, rows)

    assert count == 1
    assert campaign.total_emails == 6
    db.commit.assert_called_once()


def test_upload_recipients_all_duplicates_are_noop() -> None:
    from sqlalchemy.exc import IntegrityError

    from app.services.campaign_service import upload_recipients

    rows = [{"email": "dup1@example.com", "name": None}, {"email": "dup2@example.com", "name": None}]
    campaign = MagicMock(spec=Campaign)
    campaign.id = uuid.uuid4()
    campaign.total_emails = 4
    db = MagicMock()

    conflict = IntegrityError("INSERT", {}, Exception("duplicate key"))
    db.flush.side_effect = [conflict, conflict, conflict]

    count = upload_recipients(db, campaign, rows)

    assert count == 0
    assert campaign.total_emails == 4
    db.commit.assert_called_once()


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



