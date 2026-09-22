"""API routers package."""

from __future__ import annotations

from app.api.v1.campaigns import router as campaigns_router
from app.api.v1.emails import router as emails_router

__all__ = ["campaigns_router", "emails_router"]
