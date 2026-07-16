"""leads, bookings, ticket brand_id (CARD-36 / CARD-39)

Revision ID: f6c0b5e8a3d1
Revises: e5b9a3d4c1f2
Create Date: 2026-07-16

"""

from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "f6c0b5e8a3d1"
down_revision: Union[str, Sequence[str], None] = "e5b9a3d4c1f2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "support_tickets",
        sa.Column("brand_id", sa.Integer(), sa.ForeignKey("brands.id", ondelete="SET NULL"), nullable=True),
    )
    op.create_index("ix_support_tickets_brand", "support_tickets", ["brand_id"])

    op.create_table(
        "leads",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("brand_id", sa.Integer(), sa.ForeignKey("brands.id", ondelete="CASCADE"), nullable=False),
        sa.Column("store_id", sa.Integer(), sa.ForeignKey("stores.id", ondelete="SET NULL"), nullable=True),
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.telegram_id", ondelete="SET NULL"), nullable=True),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("phone", sa.String(length=50), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("preferred_channel", sa.String(length=20), nullable=False, server_default="phone"),
        sa.Column("channel_handle", sa.String(length=128), nullable=True),
        sa.Column("interest_type", sa.String(length=40), nullable=True),
        sa.Column("item_slug", sa.String(length=120), nullable=True),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("source", sa.String(length=40), nullable=False, server_default="web_site"),
        sa.Column("utm_json", sa.JSON(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="new"),
        sa.Column("consent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("age_confirmed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_leads_brand_id", "leads", ["brand_id"])
    op.create_index("ix_leads_store_id", "leads", ["store_id"])
    op.create_index("ix_leads_user_id", "leads", ["user_id"])
    op.create_index("ix_leads_status", "leads", ["status"])

    op.create_table(
        "bookings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("brand_id", sa.Integer(), sa.ForeignKey("brands.id", ondelete="CASCADE"), nullable=False),
        sa.Column("store_id", sa.Integer(), sa.ForeignKey("stores.id", ondelete="SET NULL"), nullable=True),
        sa.Column("lead_id", sa.Integer(), sa.ForeignKey("leads.id", ondelete="SET NULL"), nullable=True),
        sa.Column("user_id", sa.BigInteger(), sa.ForeignKey("users.telegram_id", ondelete="SET NULL"), nullable=True),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("phone", sa.String(length=50), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("meeting_type", sa.String(length=20), nullable=False, server_default="in_person"),
        sa.Column("preferred_slots", sa.JSON(), nullable=True),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("meet_url", sa.String(length=512), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="requested"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_bookings_brand_id", "bookings", ["brand_id"])
    op.create_index("ix_bookings_store_id", "bookings", ["store_id"])
    op.create_index("ix_bookings_user_id", "bookings", ["user_id"])
    op.create_index("ix_bookings_status", "bookings", ["status"])


def downgrade() -> None:
    op.drop_index("ix_bookings_status", table_name="bookings")
    op.drop_index("ix_bookings_user_id", table_name="bookings")
    op.drop_index("ix_bookings_store_id", table_name="bookings")
    op.drop_index("ix_bookings_brand_id", table_name="bookings")
    op.drop_table("bookings")

    op.drop_index("ix_leads_status", table_name="leads")
    op.drop_index("ix_leads_user_id", table_name="leads")
    op.drop_index("ix_leads_store_id", table_name="leads")
    op.drop_index("ix_leads_brand_id", table_name="leads")
    op.drop_table("leads")

    op.drop_index("ix_support_tickets_brand", table_name="support_tickets")
    op.drop_column("support_tickets", "brand_id")
