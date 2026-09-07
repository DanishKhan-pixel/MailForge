"""Unit tests for database session manager dependency."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from app.db.session import get_db


@patch("app.db.session.SessionLocal")
def test_get_db_yields_and_closes_session(mock_session_local: MagicMock) -> None:
    mock_session_instance = MagicMock()
    mock_session_local.return_value = mock_session_instance

    gen = get_db()
    session = next(gen)
    assert session == mock_session_instance

    # Finalize generator context
    try:
        next(gen)
    except StopIteration:
        pass

    mock_session_instance.close.assert_called_once()
