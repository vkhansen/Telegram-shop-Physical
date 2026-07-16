"""Backfill user_identities for Telegram users (CARD-30)

Revision ID: a1c30b0e4d2f
Revises: f6c0b5e8a3d1
Create Date: 2026-07-17

Table ``user_identities`` already created by e5b9a3d4c1f2 (CARD-39).
This migration only backfills platform=telegram rows for existing users.
"""

from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "a1c30b0e4d2f"
down_revision: Union[str, Sequence[str], None] = "f6c0b5e8a3d1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    # Insert telegram identities for users that do not yet have one
    conn.execute(
        sa.text(
            """
            INSERT INTO user_identities (user_id, platform, external_id)
            SELECT u.telegram_id, 'telegram', CAST(u.telegram_id AS VARCHAR)
            FROM users u
            WHERE NOT EXISTS (
                SELECT 1 FROM user_identities ui
                WHERE ui.platform = 'telegram'
                  AND ui.external_id = CAST(u.telegram_id AS VARCHAR)
            )
            """
        )
    )


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text("DELETE FROM user_identities WHERE platform = 'telegram'"))
