"""Configuration loader powered by environment variables."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """App settings loaded from .env and OS environment."""

    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: str
    smtp_password: str
    smtp_from_email: str
    retry_count: int = 2

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
