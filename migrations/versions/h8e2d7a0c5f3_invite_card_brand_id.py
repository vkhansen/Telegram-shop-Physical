"""brand_id on reference_codes for branded invite sheets

Revision ID: h8e2d7a0c5f3
Revises: g7d1c6f9b4e2
Create Date: 2026-07-17
"""

from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "h8e2d7a0c5f3"
down_revision: Union[str, Sequence[str], None] = "g7d1c6f9b4e2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "reference_codes",
        sa.Column("brand_id", sa.Integer(), sa.ForeignKey("brands.id", ondelete="SET NULL"), nullable=True),
    )
    op.create_index("ix_reference_codes_brand_id", "reference_codes", ["brand_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_reference_codes_brand_id", table_name="reference_codes")
    op.drop_column("reference_codes", "brand_id")
