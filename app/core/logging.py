"""Logging configuration for API and workers."""

from __future__ import annotations

import logging
from logging.config import dictConfig
from logging.handlers import RotatingFileHandler
from pathlib import Path

from app.core.config import settings


def configure_logging(log_level: str = "INFO") -> None:
    """Configure structured console and rotating file logging for API and workers.

    Args:
        log_level: Logging severity level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
    """
    log_dir = Path(settings.log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file_path = log_dir / settings.log_file_name
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
                    "class": "logging.handlers.RotatingFileHandler",
                    "filename": str(log_file_path),
                    "formatter": "standard",
                    "maxBytes": settings.log_max_bytes,
                    "backupCount": settings.log_backup_count,
                },
            },
            "root": {"handlers": ["console", "file"], "level": log_level.upper()},
        }
    )
    logging.getLogger(__name__).info("Logging configured with level %s", log_level.upper())


