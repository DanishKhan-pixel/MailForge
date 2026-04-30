"""Logging configuration for API and workers."""

import logging
from logging.config import dictConfig
from pathlib import Path


def configure_logging() -> None:
    """Configure structured console and file logs."""
    Path("logs").mkdir(parents=True, exist_ok=True)
    dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "standard": {
                    "format": "%(asctime)s %(levelname)s %(name)s - %(message)s",
                }
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "standard",
                },
                "file": {
                    "class": "logging.FileHandler",
                    "filename": "logs/email_automation.log",
                    "formatter": "standard",
                },
            },
            "root": {"handlers": ["console", "file"], "level": "INFO"},
        }
    )
    logging.getLogger(__name__).info("Logging configured")
