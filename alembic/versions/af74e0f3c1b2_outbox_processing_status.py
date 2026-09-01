"""add processing status and lease to outbox

Revision ID: af74e0f3c1b2
Revises: 9d3b8cc9a1e2
Create Date: 2026-08-28 16:35:00.000000
"""

from alembic import op
import sqlalchemy as sa

revision = "af74e0f3c1b2"
down_revision = "9d3b8cc9a1e2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TYPE outbox_status ADD VALUE IF NOT EXISTS 'processing'")
    op.add_column(
        "outbox",
        sa.Column("locked_until", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_outbox_dispatch_lock",
        "outbox",
        ["status", "backoff_delay", "locked_until", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_outbox_dispatch_lock", table_name="outbox")
    op.drop_column("outbox", "locked_until")
    # PostgreSQL enums cannot remove a single value in-place safely.
    # Keep the enum change forward-only.
