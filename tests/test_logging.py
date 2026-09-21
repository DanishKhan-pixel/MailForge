"""Unit tests for logging configuration module."""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from app.core.config import settings
from app.core.logging import configure_logging


def test_configure_logging_creates_logs_directory() -> None:
    configure_logging("DEBUG")
    assert Path("logs").exists()
    logger = logging.getLogger()
    assert logger.level == logging.DEBUG


def test_configure_logging_uses_rotating_file_handler() -> None:
    configure_logging("INFO")
    rotating_handlers = [
        handler
        for handler in logging.getLogger().handlers
        if isinstance(handler, RotatingFileHandler)
    ]
    assert rotating_handlers
    handler = rotating_handlers[0]
    assert handler.maxBytes == settings.log_max_bytes
    assert handler.backupCount == settings.log_backup_count
