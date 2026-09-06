"""Unit tests for Celery task helper functions."""

from __future__ import annotations

from app.workers.tasks import _render_message


def test_render_message_with_name() -> None:
    template = "Hello {name}, welcome to MailForge!"
    rendered = _render_message(template, "Alice")
    assert rendered == "Hello Alice, welcome to MailForge!"


def test_render_message_with_none_name() -> None:
    template = "Hello {name}, welcome!"
    rendered = _render_message(template, None)
    assert rendered == "Hello there, welcome!"


def test_render_message_without_placeholder() -> None:
    template = "Welcome to MailForge!"
    rendered = _render_message(template, "Bob")
    assert rendered == "Welcome to MailForge!"
