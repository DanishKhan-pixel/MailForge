"""FastAPI application entrypoint for production email campaigns."""

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.api.v1.campaigns import router as campaigns_router
from app.core.config import settings
from app.core.logging import configure_logging

configure_logging()

app = FastAPI(
    title=settings.app_name,
    version="2.0.0",
    description="Campaign-based email automation with PostgreSQL and Celery workers.",
)

app.include_router(campaigns_router)
templates = Jinja2Templates(directory="app/templates")


@app.get("/", response_class=HTMLResponse, tags=["UI"])
def dashboard(request: Request) -> HTMLResponse:
    """Serve the frontend dashboard."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/health", tags=["Health"])
def health_check() -> dict[str, str]:
    """Health check endpoint used by orchestrators."""
    return {"status": "ok"}
