"""invite cards fields on reference_codes

Revision ID: g7d1c6f9b4e2
Revises: f6c0b5e8a3d1
Create Date: 2026-07-17

Physical tear-off invite cards:
  - card_number: printed number on both halves
  - card_batch_id: print run id
  - recipient_name: written on stub when handed out
  - given_at: when the QR half was given away
"""

from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "g7d1c6f9b4e2"
down_revision: Union[str, Sequence[str], None] = "a1c30b0e4d2f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("reference_codes", sa.Column("card_number", sa.Integer(), nullable=True))
    op.add_column("reference_codes", sa.Column("card_batch_id", sa.String(length=32), nullable=True))
    op.add_column("reference_codes", sa.Column("recipient_name", sa.String(length=200), nullable=True))
    op.add_column("reference_codes", sa.Column("given_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index("ix_reference_codes_card_number", "reference_codes", ["card_number"], unique=True)
    op.create_index("ix_reference_codes_card_batch_id", "reference_codes", ["card_batch_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_reference_codes_card_batch_id", table_name="reference_codes")
    op.drop_index("ix_reference_codes_card_number", table_name="reference_codes")
    op.drop_column("reference_codes", "given_at")
    op.drop_column("reference_codes", "recipient_name")
    op.drop_column("reference_codes", "card_batch_id")
    op.drop_column("reference_codes", "card_number")
