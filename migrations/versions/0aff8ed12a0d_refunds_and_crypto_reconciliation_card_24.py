"""refunds + crypto reconciliation (CARD-24)

Adds the money-safety schema for CARD-24:
  * ``refunds`` table — audit trail for payment reversals
  * ``orders.refund_status`` — reversal state on the order
  * ``crypto_payments.overpaid_amount`` — overpayment delta in native coin units

Revision ID: 0aff8ed12a0d
Revises: 616a5683e747
Create Date: 2026-06-03 00:00:00.000000

"""

from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0aff8ed12a0d"
down_revision: Union[str, Sequence[str], None] = "616a5683e747"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "refunds",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("order_id", sa.Integer(), nullable=False),
        sa.Column("method", sa.String(length=20), nullable=False),
        sa.Column("bonus_restored", sa.Numeric(precision=12, scale=2), nullable=False, server_default="0"),
        sa.Column("amount", sa.Numeric(precision=12, scale=2), nullable=False, server_default="0"),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="completed"),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("created_by", sa.BigInteger(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("status IN ('completed', 'pending_manual')", name="ck_refunds_status"),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_refunds_order_id", "refunds", ["order_id"], unique=False)

    op.add_column("orders", sa.Column("refund_status", sa.String(length=20), nullable=True))
    op.add_column(
        "crypto_payments",
        sa.Column("overpaid_amount", sa.Numeric(precision=20, scale=8), nullable=True, server_default="0"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("crypto_payments", "overpaid_amount")
    op.drop_column("orders", "refund_status")
    op.drop_index("ix_refunds_order_id", table_name="refunds")
    op.drop_table("refunds")
