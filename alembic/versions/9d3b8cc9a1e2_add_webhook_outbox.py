"""add durable webhook outbox

Revision ID: 9d3b8cc9a1e2
Revises: 2838d0a6db39
Create Date: 2026-08-28 14:50:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "9d3b8cc9a1e2"
down_revision = "2838d0a6db39"
branch_labels = None
depends_on = None


webhook_status = sa.Enum(
    "pending",
    "processing",
    "delivered",
    "failed",
    name="webhook_delivery_status",
)


def upgrade() -> None:
    op.create_table(
        "webhook_outbox",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("payment_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("target_url", sa.String(length=2048), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "status",
            webhook_status,
            server_default="pending",
            nullable=False,
        ),
        sa.Column("retry_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("next_attempt_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("locked_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_webhook_outbox_payment_id",
        "webhook_outbox",
        ["payment_id"],
        unique=False,
    )
    op.create_index(
        "ix_webhook_outbox_dispatch",
        "webhook_outbox",
        ["status", "next_attempt_at", "locked_until"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_webhook_outbox_dispatch", table_name="webhook_outbox")
    op.drop_index("ix_webhook_outbox_payment_id", table_name="webhook_outbox")
    op.drop_table("webhook_outbox")
    webhook_status.drop(op.get_bind(), checkfirst=True)
