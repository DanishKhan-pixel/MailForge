"""Application configuration loaded from environment variables."""

from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Centralized runtime configuration."""

    app_name: str = "Email Automation System"
    app_version: str = "2.0.0"
    app_env: str = "development"

    # Defaults allow local UI/API verification without full infra env setup.
    database_url: str = Field(
        "postgresql+psycopg://mailforge:mailforge@localhost:5432/mailforge",
        alias="DATABASE_URL",
    )
    redis_url: str = Field("redis://localhost:6379/0", alias="REDIS_URL")
    celery_result_backend: str = Field("redis://localhost:6379/1", alias="CELERY_RESULT_BACKEND")

    smtp_host: str = Field("smtp.gmail.com", alias="SMTP_HOST")
    smtp_port: int = Field(587, alias="SMTP_PORT", ge=1, le=65535)
    smtp_username: str = Field("", alias="SMTP_USERNAME")
    smtp_password: str = Field("", alias="SMTP_PASSWORD")
    smtp_from_email: str = Field("no-reply@example.com", alias="SMTP_FROM_EMAIL")
    smtp_timeout: int = Field(30, alias="SMTP_TIMEOUT", ge=1, le=120)

    send_delay_seconds: int = Field(4, alias="SEND_DELAY_SECONDS", ge=3, le=5)
    retry_count: int = Field(3, alias="RETRY_COUNT", ge=0, le=3)

    log_dir: str = Field("logs", alias="LOG_DIR")
    log_file_name: str = Field("email_automation.log", alias="LOG_FILE_NAME")
    log_max_bytes: int = Field(5 * 1024 * 1024, alias="LOG_MAX_BYTES", ge=1024)
    log_backup_count: int = Field(5, alias="LOG_BACKUP_COUNT", ge=0, le=50)

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def is_development(self) -> bool:
        """Check if application is running in development mode."""
        return self.app_env.lower() in ("dev", "development")

    @property
    def is_production(self) -> bool:
        """Check if application is running in production mode."""
        return self.app_env.lower() in ("prod", "production")

    @property
    def max_retries_limit(self) -> int:
        """Get the configured retry count limit."""
        return self.retry_count

    @property
    def app_description(self) -> str:
        """Get descriptive documentation overview of the application."""
        return "Campaign-based email automation with PostgreSQL and Celery workers."

    @property
    def is_debug(self) -> bool:
        """Check if application operates in debug mode (alias for development mode)."""
        return self.is_development





settings = Settings()

