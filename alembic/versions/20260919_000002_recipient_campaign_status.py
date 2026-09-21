"""add composite campaign status index on recipients

Revision ID: 20260919_000002
Revises: 20260919_000001
Create Date: 2026-09-19 13:00:00
"""

from __future__ import annotations

from alembic import op

# revision identifiers, used by Alembic.
revision = "20260919_000002"
down_revision = "20260919_000001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index("ix_recipients_campaign_status", "recipients", ["campaign_id", "status"])


def downgrade() -> None:
    op.drop_index("ix_recipients_campaign_status", table_name="recipients")