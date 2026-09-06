"""Unit tests for recipient CSV parsing service."""

from __future__ import annotations

import io
import pytest
from fastapi import HTTPException, UploadFile

from app.services.csv_service import parse_recipients_csv


@pytest.mark.asyncio
async def test_parse_recipients_csv_valid() -> None:
    content = b"email,name\nalice@example.com,Alice\nbob@example.com,Bob\n"
    file = UploadFile(filename="recipients.csv", file=io.BytesIO(content))
    result = await parse_recipients_csv(file)
    assert len(result) == 2
    assert result[0] == {"email": "alice@example.com", "name": "Alice"}
    assert result[1] == {"email": "bob@example.com", "name": "Bob"}


@pytest.mark.asyncio
async def test_parse_recipients_csv_deduplication() -> None:
    content = b"email,name\nalice@example.com,Alice\nALICE@example.com,Alice Duplicate\n"
    file = UploadFile(filename="recipients.csv", file=io.BytesIO(content))
    result = await parse_recipients_csv(file)
    assert len(result) == 1
    assert result[0]["email"] == "alice@example.com"


@pytest.mark.asyncio
async def test_parse_recipients_csv_invalid_extension() -> None:
    file = UploadFile(filename="recipients.txt", file=io.BytesIO(b"data"))
    with pytest.raises(HTTPException) as exc_info:
        await parse_recipients_csv(file)
    assert exc_info.value.status_code == 400
    assert "Only CSV files" in exc_info.value.detail


@pytest.mark.asyncio
async def test_parse_recipients_csv_empty_file() -> None:
    file = UploadFile(filename="recipients.csv", file=io.BytesIO(b""))
    with pytest.raises(HTTPException) as exc_info:
        await parse_recipients_csv(file)
    assert exc_info.value.status_code == 400
    assert "empty" in exc_info.value.detail


@pytest.mark.asyncio
async def test_parse_recipients_csv_missing_email_header() -> None:
    file = UploadFile(filename="recipients.csv", file=io.BytesIO(b"name,age\nAlice,30\n"))
    with pytest.raises(HTTPException) as exc_info:
        await parse_recipients_csv(file)
    assert exc_info.value.status_code == 400
    assert "email" in exc_info.value.detail
