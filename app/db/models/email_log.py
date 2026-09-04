"""Email log ORM model."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class EmailLog(Base):
    """Stores attempt-level email delivery logs."""

    __tablename__ = "email_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    recipient_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("recipients.id", ondelete="CASCADE"), index=True, nullable=False
    )
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    response: Mapped[str | None] = mapped_column(Text, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    recipient = relationship("Recipient", back_populates="logs")

    def __repr__(self) -> str:
        return f"<EmailLog(id={self.id}, recipient_id={self.recipient_id}, status={self.status!r})>"

