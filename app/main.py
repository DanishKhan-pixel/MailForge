"""FastAPI application entrypoint for production email campaigns."""

from __future__ import annotations

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.v1.campaigns import router as campaigns_router
from app.api.v1.emails import router as emails_router
from app.core.config import settings
from app.core.logging import configure_logging
from app.core.middleware import RequestIdMiddleware, RequestLoggingMiddleware
from app.db.session import get_db
from app.schemas.common import HealthResponse, ReadyResponse


configure_logging()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=settings.app_description,
    openapi_tags=[
        {"name": "Campaigns", "description": "Operations for managing and triggering email campaigns."},
        {"name": "Emails", "description": "Single-email dispatch operations."},
        {"name": "Health", "description": "System health and status endpoints."},
        {"name": "UI", "description": "Web frontend user interface dashboard pages."},
    ],
)

app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(RequestIdMiddleware)


app.include_router(campaigns_router)
app.include_router(emails_router)
templates = Jinja2Templates(directory="app/templates")


@app.get("/", response_class=HTMLResponse, tags=["UI"])
def index(request: Request) -> HTMLResponse:
    """Serve the frontend dashboard web user interface.

    Args:
        request: Incoming HTTP request context.

    Returns:
        Rendered Jinja2 HTML template response for dashboard index.
    """
    return templates.TemplateResponse(request=request, name="index.html")


@app.get("/health", response_model=HealthResponse, tags=["Health"])
def health_check() -> HealthResponse:
    """Provide system health status for monitoring orchestrators and load balancers.

    Returns:
        HealthResponse object containing service status indicator.
    """
    return HealthResponse(status="ok")


@app.get("/ready", response_model=ReadyResponse, tags=["Health"])
def readiness_check(db: Session = Depends(get_db)) -> ReadyResponse:
    """Probe database connectivity to report service readiness.

    Args:
        db: Managed SQLAlchemy database session dependency.

    Returns:
        ReadyResponse indicating whether the service can accept traffic.

    Raises:
        HTTPException: 503 SERVICE UNAVAILABLE if database is unreachable.
    """
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        raise HTTPException(status_code=503, detail="Database unavailable.") from exc
    return ReadyResponse(status="ready")


@app.get("/dashboard", response_class=HTMLResponse, tags=["UI"])
def dashboard(request: Request) -> HTMLResponse:
    """Serve the web dashboard user interface route alias.

    Args:
        request: Incoming HTTP request context.

    Returns:
        Rendered Jinja2 HTML template response for dashboard index.
    """
    return templates.TemplateResponse(request=request, name="index.html")