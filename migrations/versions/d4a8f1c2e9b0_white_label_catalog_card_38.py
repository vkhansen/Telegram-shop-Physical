"""White-label brand/store web fields + goods flags (CARD-38 Phase A)

Revision ID: d4a8f1c2e9b0
Revises: b3f2c4e8a1d7
Create Date: 2026-07-16

"""

from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "d4a8f1c2e9b0"
down_revision: Union[str, Sequence[str], None] = "b3f2c4e8a1d7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # brands
    op.add_column("brands", sa.Column("legal_name", sa.String(length=255), nullable=True))
    op.add_column("brands", sa.Column("dbd_number", sa.String(length=64), nullable=True))
    op.add_column("brands", sa.Column("support_email", sa.String(length=255), nullable=True))
    op.add_column("brands", sa.Column("support_phone", sa.String(length=50), nullable=True))
    op.add_column(
        "brands",
        sa.Column("commerce_mode", sa.String(length=20), nullable=False, server_default="full_store"),
    )
    op.add_column(
        "brands",
        sa.Column("age_gate_enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column("brands", sa.Column("min_age", sa.Integer(), nullable=True))
    op.add_column("brands", sa.Column("web_profile", sa.JSON(), nullable=True))

    # stores
    op.add_column("stores", sa.Column("slug", sa.String(length=80), nullable=True))
    op.add_column("stores", sa.Column("web_profile", sa.JSON(), nullable=True))
    op.create_index("ix_stores_slug", "stores", ["slug"], unique=False)
    op.create_index("ix_stores_brand_slug", "stores", ["brand_id", "slug"], unique=False)

    # Backfill store slugs from name (simple ASCII slug)
    conn = op.get_bind()
    rows = conn.execute(sa.text("SELECT id, brand_id, name FROM stores")).fetchall()
    used: dict[tuple, set[str]] = {}
    for row in rows:
        store_id, brand_id, name = row[0], row[1], row[2] or "store"
        base = "".join(c if c.isalnum() else "-" for c in name.lower()).strip("-")
        while "--" in base:
            base = base.replace("--", "-")
        base = (base or "store")[:70]
        key = brand_id
        used.setdefault(key, set())
        slug = base
        n = 2
        while slug in used[key]:
            slug = f"{base}-{n}"
            n += 1
        used[key].add(slug)
        conn.execute(
            sa.text("UPDATE stores SET slug = :slug WHERE id = :id"),
            {"slug": slug, "id": store_id},
        )

    op.create_unique_constraint("uq_store_brand_slug", "stores", ["brand_id", "slug"])

    # goods web flags
    op.add_column(
        "goods",
        sa.Column("web_listable", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.add_column(
        "goods",
        sa.Column("web_orderable", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.add_column(
        "goods",
        sa.Column("inquiry_only", sa.Boolean(), nullable=False, server_default=sa.false()),
    )


def downgrade() -> None:
    op.drop_column("goods", "inquiry_only")
    op.drop_column("goods", "web_orderable")
    op.drop_column("goods", "web_listable")

    op.drop_constraint("uq_store_brand_slug", "stores", type_="unique")
    op.drop_index("ix_stores_brand_slug", table_name="stores")
    op.drop_index("ix_stores_slug", table_name="stores")
    op.drop_column("stores", "web_profile")
    op.drop_column("stores", "slug")

    op.drop_column("brands", "web_profile")
    op.drop_column("brands", "min_age")
    op.drop_column("brands", "age_gate_enabled")
    op.drop_column("brands", "commerce_mode")
    op.drop_column("brands", "support_phone")
    op.drop_column("brands", "support_email")
    op.drop_column("brands", "dbd_number")
    op.drop_column("brands", "legal_name")
