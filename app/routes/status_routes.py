"""Routes for reading current background job status."""

from fastapi import APIRouter

from app.models.schemas import StatusResponse
from app.services.state_service import state

router = APIRouter()


@router.get("/status", response_model=StatusResponse)
def get_status() -> StatusResponse:
    """Return current sending progress."""
    with state.lock:
        current = state.status
        return StatusResponse(
            is_running=current.is_running,
            total=current.total,
            success_count=current.success_count,
            failed_count=current.failed_count,
            last_error=current.last_error,
        )
