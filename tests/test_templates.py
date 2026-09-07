"""Unit tests for HTML template rendering accessibility tags."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_index_template_contains_aria_attributes() -> None:
    response = client.get("/")
    assert response.status_code == 200
    html = response.text
    assert 'role="progressbar"' in html
    assert 'aria-live="polite"' in html
    assert "Campaign Progress" in html
