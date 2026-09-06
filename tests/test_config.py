"""Unit tests for Settings and environment configuration."""

from __future__ import annotations

from app.core.config import Settings


def test_settings_default_values() -> None:
    settings = Settings()
    assert settings.app_name == "Email Automation System"
    assert settings.send_delay_seconds >= 3
    assert settings.retry_count <= 3


def test_is_development_property() -> None:
    dev_settings = Settings(app_env="development")
    assert dev_settings.is_development is True

    dev_short = Settings(app_env="dev")
    assert dev_short.is_development is True

    prod_settings = Settings(app_env="production")
    assert prod_settings.is_development is False
