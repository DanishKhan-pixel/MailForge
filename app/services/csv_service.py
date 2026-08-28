
import csv
import io

from fastapi import HTTPException, UploadFile, status
from pydantic import EmailStr, TypeAdapter, ValidationError

email_adapter = TypeAdapter(EmailStr)


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

    reader = csv.DictReader(io.StringIO(decoded))
    if not reader.fieldnames or "email" not in reader.fieldnames:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="CSV must include an 'email' column.")

    rows: list[dict[str, str]] = []
    invalid_rows: list[int] = []

    for idx, row in enumerate(reader, start=2):
        email = (row.get("email") or "").strip()
        name = (row.get("name") or "").strip()
        if not email:
            invalid_rows.append(idx)
            continue
        try:
            normalized_email = _validate_email(email)
        except ValueError:
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

    # Deduplicate recipients: keep first occurrence, preserve order
    unique_rows: dict[str, dict[str, str]] = {}
    seen_emails: set[str] = set()
    deduplicated_rows: list[dict[str, str]] = []
    
    for row in rows:
        email = row["email"].lower()
        if email not in seen_emails:
            unique_rows[email] = row
            seen_emails.add(email)
            deduplicated_rows.append(row)
    
    if len(deduplicated_rows) < len(rows):
        # Log deduplication if needed (optional)
        pass

