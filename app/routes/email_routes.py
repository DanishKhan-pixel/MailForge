"""Routes for starting background email sending."""

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status

from app.models.schemas import SendEmailRequest
from app.services.email_service import send_emails_in_background
from app.services.state_service import reset_status, state
from app.utils.rate_limit import rate_limit

router = APIRouter()


@router.post("/send-emails", dependencies=[Depends(rate_limit(max_requests=5, window_seconds=60))])
def send_emails(request: SendEmailRequest, background_tasks: BackgroundTasks) -> dict[str, str | int]:
    """Trigger background email sending for previously uploaded recipients."""
    with state.lock:
        recipients_count = len(state.recipients)
        is_running = state.status.is_running

    if recipients_count == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No recipients found. Upload a CSV first.",
        )

    if is_running:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An email sending job is already running.",
        )

    reset_status(total=recipients_count)
    background_tasks.add_task(
        send_emails_in_background,
        request.subject,
        request.message,
        request.delay_seconds,
    )

    return {
        "message": "Email sending started in background.",
        "total_recipients": recipients_count,
    }
