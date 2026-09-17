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
