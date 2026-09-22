"""Unit tests for FastAPI main application entrypoint routes."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app
from app.schemas.common import HealthResponse

client = TestClient(app)


def test_index_route_status_and_content_type() -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")


def test_dashboard_route_status_and_content_type() -> None:
    response = client.get("/dashboard")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")


def test_health_check_status_code_and_json() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_health_check_matches_health_response_schema() -> None:
    response = client.get("/health")
    payload = HealthResponse.model_validate(response.json())
    assert payload.status == "ok"


def test_app_metadata_follows_settings() -> None:
    assert app.title == settings.app_name
    assert app.version == settings.app_version
    assert app.description == settings.app_description


def test_openapi_tags_metadata() -> None:
    tags = app.openapi_tags
    assert tags is not None
    tag_names = [t["name"] for t in tags]
    assert "Campaigns" in tag_names
    assert "Emails" in tag_names
    assert "Health" in tag_names
    assert "UI" in tag_names

