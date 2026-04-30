"""In-memory state store for uploaded recipients and send progress."""

from __future__ import annotations

from dataclasses import dataclass, field
from threading import Lock


@dataclass
class SendStatus:
    """Tracks progress for background email sending."""

    is_running: bool = False
    total: int = 0
    success_count: int = 0
    failed_count: int = 0
    last_error: str | None = None


@dataclass
class AppState:
    """Application-level state used by routes and services."""

    recipients: list[dict[str, str]] = field(default_factory=list)
    status: SendStatus = field(default_factory=SendStatus)
    lock: Lock = field(default_factory=Lock)


state = AppState()


def reset_status(total: int) -> None:
    """Reset status before starting a new sending run."""
    with state.lock:
        state.status = SendStatus(is_running=True, total=total)


def mark_success() -> None:
    """Increment successful send counter."""
    with state.lock:
        state.status.success_count += 1


def mark_failure(error_message: str) -> None:
    """Increment failed send counter and keep the latest error."""
    with state.lock:
        state.status.failed_count += 1
        state.status.last_error = error_message


def complete_run() -> None:
    """Mark the current sending run as completed."""
    with state.lock:
        state.status.is_running = False
