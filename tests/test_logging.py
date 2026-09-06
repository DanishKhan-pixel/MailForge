"""Unit tests for logging configuration module."""

from __future__ import annotations

import logging
from pathlib import Path

from app.core.logging import configure_logging


def test_configure_logging_creates_logs_directory() -> None:
    configure_logging("DEBUG")
    assert Path("logs").exists()
    logger = logging.getLogger()
    assert logger.level == logging.DEBUG
