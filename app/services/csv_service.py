"""Service functions for reading and validating CSV uploads."""

from __future__ import annotations

import csv
import io

from fastapi import HTTPException, UploadFile, status

from app.utils.email_validator import is_valid_email


async def parse_recipients_csv(file: UploadFile) -> list[dict[str, str]]:
    """Parse recipient rows from CSV and validate required fields."""
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only CSV files are supported.",
        )

    raw_content = await file.read()
    if not raw_content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )

    try:
        decoded = raw_content.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CSV must be UTF-8 encoded.",
        ) from exc

    reader = csv.DictReader(io.StringIO(decoded))
    if not reader.fieldnames or "email" not in reader.fieldnames:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CSV must include an 'email' column.",
        )

    recipients: list[dict[str, str]] = []
    invalid_rows: list[int] = []

    for idx, row in enumerate(reader, start=2):
        email = (row.get("email") or "").strip()
        name = (row.get("name") or "").strip()

        if not email or not is_valid_email(email):
            invalid_rows.append(idx)
            continue

        recipients.append({"email": email, "name": name})

    if invalid_rows:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid email format found in rows: {invalid_rows}",
        )

    if not recipients:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid recipient emails found in CSV.",
        )

    return recipients
