"""add case-insensitive unique index on campaign recipients

Revision ID: 20260919_000001
Revises: 20260430_000001
Create Date: 2026-09-19 12:00:00
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "20260919_000001"
down_revision = "20260430_000001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()

    bind.execute(
        sa.text(
            """
            DELETE FROM recipients a
            USING recipients b
            WHERE a.id > b.id
              AND a.campaign_id = b.campaign_id
              AND LOWER(a.email) = LOWER(b.email)
            """
        )
    )

    op.create_index(
        "uq_recipients_campaign_email",
        "recipients",
        ["campaign_id", sa.text("LOWER(email)")],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("uq_recipients_campaign_email", table_name="recipients")