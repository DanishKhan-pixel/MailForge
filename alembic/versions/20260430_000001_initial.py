"""initial campaign schema

Revision ID: 20260430_000001
Revises:
Create Date: 2026-04-30 13:40:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20260430_000001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    campaign_status = sa.Enum("pending", "running", "completed", name="campaign_status")
    recipient_status = sa.Enum("pending", "sent", "failed", name="recipient_status")
    campaign_status.create(op.get_bind(), checkfirst=True)
    recipient_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "campaigns",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("subject", sa.String(length=200), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("total_emails", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("sent_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("failed_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", campaign_status, nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "recipients",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("campaign_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=True),
        sa.Column("status", recipient_status, nullable=False, server_default="pending"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["campaign_id"], ["campaigns.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_recipients_campaign_id", "recipients", ["campaign_id"])
    op.create_index("ix_recipients_email", "recipients", ["email"])

    op.create_table(
        "email_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("recipient_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("response", sa.Text(), nullable=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["recipient_id"], ["recipients.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_email_logs_recipient_id", "email_logs", ["recipient_id"])


def downgrade() -> None:
    op.drop_index("ix_email_logs_recipient_id", table_name="email_logs")
    op.drop_table("email_logs")
    op.drop_index("ix_recipients_email", table_name="recipients")
    op.drop_index("ix_recipients_campaign_id", table_name="recipients")
    op.drop_table("recipients")
    op.drop_table("campaigns")
    sa.Enum(name="recipient_status").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="campaign_status").drop(op.get_bind(), checkfirst=True)
