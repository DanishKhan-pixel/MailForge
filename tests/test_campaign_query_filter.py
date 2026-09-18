"""Unit tests for CampaignQueryFilter Pydantic schema."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.schemas.campaign import CampaignQueryFilter


def test_campaign_query_filter_defaults() -> None:
    filter_obj = CampaignQueryFilter()
    assert filter_obj.page == 1
    assert filter_obj.page_size == 10
    assert filter_obj.status is None


def test_campaign_query_filter_custom() -> None:
    filter_obj = CampaignQueryFilter(page=2, page_size=50, status="running")
    assert filter_obj.page == 2
    assert filter_obj.page_size == 50
    assert filter_obj.status == "running"


def test_campaign_query_filter_validation() -> None:
    with pytest.raises(ValidationError):
        CampaignQueryFilter(page=0)

    with pytest.raises(ValidationError):
        CampaignQueryFilter(page_size=200)


def test_campaign_stats_schema() -> None:
    from app.schemas.campaign import CampaignStats

    stats = CampaignStats()
    assert stats.total_campaigns == 0
    assert stats.total_emails_sent == 0
    assert stats.total_emails_failed == 0

    custom_stats = CampaignStats(total_campaigns=5, total_emails_sent=500, total_emails_failed=12)
    assert custom_stats.total_campaigns == 5
    assert custom_stats.total_emails_sent == 500
    assert custom_stats.total_emails_failed == 12

    with pytest.raises(ValidationError):
        CampaignStats(total_campaigns=-1)
