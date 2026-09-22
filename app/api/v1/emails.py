"""Single-email dispatch API routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.core.rate_limit import rate_limit
from app.schemas.common import MessageResponse
from app.schemas.recipient import EmailPayload
from app.services.email_service import EmailService

router = APIRouter(prefix="/emails", tags=["Emails"])

email_service = EmailService()


@router.post(
    "",
    response_model=MessageResponse,
    dependencies=[Depends(rate_limit(20, 60))],
)
def send_email_endpoint(payload: EmailPayload) -> MessageResponse:
    """Dispatch a single outbound email message via SMTP."""
    email_service.send_email(str(payload.recipient), payload.subject, payload.body)
    return MessageResponse(message="Email sent successfully.")