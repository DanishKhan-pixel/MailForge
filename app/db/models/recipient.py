"""Recipient ORM model."""

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class RecipientStatus(str, enum.Enum):
    pending = "pending"
    sent = "sent"
    failed = "failed"


class Recipient(Base):
    """Stores recipients belonging to a campaign."""

    __tablename__ = "recipients"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    campaign_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("campaigns.id", ondelete="CASCADE"), index=True, nullable=False
    )
    email: Mapped[str] = mapped_column(String(320), index=True, nullable=False)
    name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    status: Mapped[RecipientStatus] = mapped_column(
        Enum(RecipientStatus, name="recipient_status"), nullable=False, default=RecipientStatus.pending
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    campaign = relationship("Campaign", back_populates="recipients")
    logs = relationship("EmailLog", back_populates="recipient", cascade="all, delete-orphan")
