from __future__ import annotations

import csv
import io

from fastapi import HTTPException, UploadFile, status
from pydantic import EmailStr, TypeAdapter, ValidationError

email_adapter = TypeAdapter(EmailStr)


MAX_CSV_RECIPIENTS = 5000
MAX_EMAIL_LENGTH = 320
MAX_NAME_LENGTH = 200
UTF8_BOM = "\ufeff"


def _validate_email(raw_email: str) -> str:
    try:
        return str(email_adapter.validate_python(raw_email))
    except ValidationError as exc:
        raise ValueError(str(exc)) from exc


async def parse_recipients_csv(file: UploadFile) -> list[dict[str, str]]:
    """Parse and validate recipient records from uploaded CSV."""
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only CSV files are supported.")

    raw_content = await file.read()
    if not raw_content:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty.")

    try:
        decoded = raw_content.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="CSV must be UTF-8 encoded.") from exc

    if decoded.startswith(UTF8_BOM):
        decoded = decoded[len(UTF8_BOM):]

    reader = csv.DictReader(io.StringIO(decoded))
    if not reader.fieldnames or "email" not in reader.fieldnames:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="CSV must include an 'email' column.")

    rows: list[dict[str, str]] = []
    invalid_rows: list[int] = []

    for idx, row in enumerate(reader, start=2):
        email = (row.get("email") or "").strip()
        name = (row.get("name") or "").strip()[:MAX_NAME_LENGTH]
        if not email:
            invalid_rows.append(idx)
            continue
        try:
            normalized_email = _validate_email(email)
        except ValueError:
            invalid_rows.append(idx)
            continue
        if len(normalized_email) > MAX_EMAIL_LENGTH:
            invalid_rows.append(idx)
            continue
        rows.append({"email": normalized_email, "name": name})

    if invalid_rows:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid emails found in rows: {invalid_rows}",
        )
    if not rows:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No valid recipients found.")
    if len(rows) > MAX_CSV_RECIPIENTS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"CSV recipient count exceeds maximum threshold of {MAX_CSV_RECIPIENTS}.",
        )

    # Deduplicate recipients case-insensitively: keep first occurrence, preserve order
    seen_emails: set[str] = set()
    deduplicated_rows: list[dict[str, str]] = []
    for row in rows:
        if row["email"].lower() not in seen_emails:
            seen_emails.add(row["email"].lower())
            deduplicated_rows.append(row)

    return deduplicated_rows
