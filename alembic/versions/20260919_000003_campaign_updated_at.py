"""add updated_at timestamp to campaigns

Revision ID: 20260919_000003
Revises: 20260919_000002
Create Date: 2026-09-19 14:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20260919_000003"
down_revision = "20260919_000002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "campaigns",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("campaigns", "updated_at")