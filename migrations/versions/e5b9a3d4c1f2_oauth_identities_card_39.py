"""OAuth identities + profiles for web ticket portal (CARD-39)

Revision ID: e5b9a3d4c1f2
Revises: d4a8f1c2e9b0
Create Date: 2026-07-16

"""

from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "e5b9a3d4c1f2"
down_revision: Union[str, Sequence[str], None] = "d4a8f1c2e9b0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "user_identities",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.telegram_id", ondelete="CASCADE"), nullable=False),
        sa.Column("platform", sa.String(length=20), nullable=False),
        sa.Column("external_id", sa.String(length=128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("platform", "external_id", name="uq_user_identities_platform_ext"),
    )
    op.create_index("ix_user_identities_user_id", "user_identities", ["user_id"])

    op.create_table(
        "oauth_profiles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.telegram_id", ondelete="CASCADE"), nullable=False),
        sa.Column("provider", sa.String(length=32), nullable=False),
        sa.Column("provider_subject", sa.String(length=128), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("email_verified", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("display_name", sa.String(length=255), nullable=True),
        sa.Column("username", sa.String(length=128), nullable=True),
        sa.Column("avatar_url", sa.String(length=512), nullable=True),
        sa.Column("raw_claims", sa.JSON(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("provider", "provider_subject", name="uq_oauth_provider_subject"),
    )
    op.create_index("ix_oauth_profiles_user_id", "oauth_profiles", ["user_id"])
    op.create_index("ix_oauth_profiles_email", "oauth_profiles", ["email"])


def downgrade() -> None:
    op.drop_index("ix_oauth_profiles_email", table_name="oauth_profiles")
    op.drop_index("ix_oauth_profiles_user_id", table_name="oauth_profiles")
    op.drop_table("oauth_profiles")
    op.drop_index("ix_user_identities_user_id", table_name="user_identities")
    op.drop_table("user_identities")
