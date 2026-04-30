"""SQLAlchemy declarative base and model imports."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all ORM models."""


# Import models for Alembic autogenerate discovery.
from app.db.models.campaign import Campaign  # noqa: E402,F401
from app.db.models.recipient import Recipient  # noqa: E402,F401
from app.db.models.email_log import EmailLog  # noqa: E402,F401
