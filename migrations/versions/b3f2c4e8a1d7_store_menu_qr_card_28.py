"""per-store menu image + payment QR (CARD-28)

Adds four nullable columns to ``stores`` so each branch can carry its own menu
board image and PromptPay account:
  * ``menu_image_file_id``   — branch menu board sent on store selection
  * ``promptpay_id``         — branch PromptPay id (overrides brand/global)
  * ``promptpay_name``       — branch account name (slip receiver match)
  * ``payment_qr_file_id``   — static branch QR image (fallback)

All nullable → fully backward compatible; stores with none behave as before.

Revision ID: b3f2c4e8a1d7
Revises: c7e1a2d9f0b3
Create Date: 2026-06-03 00:00:00.000000

"""

from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "b3f2c4e8a1d7"
down_revision: Union[str, Sequence[str], None] = "c7e1a2d9f0b3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("stores", sa.Column("menu_image_file_id", sa.String(length=255), nullable=True))
    op.add_column("stores", sa.Column("promptpay_id", sa.String(length=20), nullable=True))
    op.add_column("stores", sa.Column("promptpay_name", sa.String(length=200), nullable=True))
    op.add_column("stores", sa.Column("payment_qr_file_id", sa.String(length=255), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("stores", "payment_qr_file_id")
    op.drop_column("stores", "promptpay_name")
    op.drop_column("stores", "promptpay_id")
    op.drop_column("stores", "menu_image_file_id")
