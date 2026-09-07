"""SQLAlchemy declarative base model definition."""

from __future__ import annotations

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Abstract base class inherited by all ORM domain models."""

    pass

