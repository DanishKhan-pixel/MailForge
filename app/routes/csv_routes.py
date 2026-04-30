"""Routes for CSV upload and recipient parsing."""

from fastapi import APIRouter, Depends, File, UploadFile

from app.services.csv_service import parse_recipients_csv
from app.services.state_service import state
from app.utils.rate_limit import rate_limit

router = APIRouter()


@router.post("/upload-csv", dependencies=[Depends(rate_limit(max_requests=20, window_seconds=60))])
async def upload_csv(file: UploadFile = File(...)) -> dict[str, int | str]:
    """
    Upload and parse a CSV file.

    Required column: email
    Optional column: name
    """
    recipients = await parse_recipients_csv(file)
    with state.lock:
        state.recipients = recipients

    return {
        "message": "CSV uploaded and parsed successfully.",
        "recipient_count": len(recipients),
    }
