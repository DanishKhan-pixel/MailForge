"""Application configuration loaded from environment variables."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Centralized runtime configuration."""

    app_name: str = "Email Automation System"
    app_env: str = "development"
    database_url: str = Field(..., alias="DATABASE_URL")
    redis_url: str = Field(..., alias="REDIS_URL")
    celery_result_backend: str = Field(..., alias="CELERY_RESULT_BACKEND")

    smtp_host: str = Field("smtp.gmail.com", alias="SMTP_HOST")
    smtp_port: int = Field(587, alias="SMTP_PORT")
    smtp_username: str = Field(..., alias="SMTP_USERNAME")
    smtp_password: str = Field(..., alias="SMTP_PASSWORD")
    smtp_from_email: str = Field(..., alias="SMTP_FROM_EMAIL")

    send_delay_seconds: int = Field(4, alias="SEND_DELAY_SECONDS", ge=3, le=5)
    retry_count: int = Field(3, alias="RETRY_COUNT", ge=0, le=3)

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
