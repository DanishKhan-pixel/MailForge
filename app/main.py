"""FastAPI application entrypoint for the email automation system."""

from fastapi import FastAPI

from app.routes.csv_routes import router as csv_router
from app.routes.email_routes import router as email_router
from app.routes.status_routes import router as status_router
from app.utils.logger import configure_logging


configure_logging()

app = FastAPI(
    title="Email Automation System",
    version="1.0.0",
    description="Upload CSV recipients and send personalized emails safely in background.",
)

app.include_router(csv_router, prefix="/api", tags=["CSV"])
app.include_router(email_router, prefix="/api", tags=["Email"])
app.include_router(status_router, prefix="/api", tags=["Status"])


@app.get("/health", tags=["Health"])
def health_check() -> dict[str, str]:
    """Simple health check endpoint for monitoring."""
    return {"status": "ok"}
