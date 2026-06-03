"""driver matching & dispatch (CARD-26)

Adds the GPS-dispatch schema for CARD-26:
  * ``drivers`` table — driver records, approval status, availability, last position
  * ``driver_location_trail`` table — append-only live-location breadcrumbs

``Order.driver_id`` (a Telegram id) already exists and is reused as the link to
the assigned driver, so no change to ``orders`` is required.

Revision ID: c7e1a2d9f0b3
Revises: 0aff8ed12a0d
Create Date: 2026-06-03 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = 'c7e1a2d9f0b3'
down_revision: Union[str, Sequence[str], None] = '0aff8ed12a0d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'drivers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('telegram_id', sa.BigInteger(), nullable=False),
        sa.Column('brand_id', sa.Integer(), nullable=True),
        sa.Column('name', sa.String(length=120), nullable=False),
        sa.Column('phone', sa.String(length=50), nullable=True),
        sa.Column('vehicle_type', sa.String(length=30), nullable=True),
        sa.Column('service_zones', sa.JSON(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='pending'),
        sa.Column('approved_by', sa.BigInteger(), nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_online', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('is_available', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('active_order_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('rating', sa.Numeric(precision=3, scale=2), nullable=True),
        sa.Column('last_latitude', sa.Float(), nullable=True),
        sa.Column('last_longitude', sa.Float(), nullable=True),
        sa.Column('last_location_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint(
            "status IN ('pending', 'approved', 'rejected', 'suspended')",
            name='ck_drivers_status',
        ),
        sa.ForeignKeyConstraint(['telegram_id'], ['users.telegram_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['brand_id'], ['brands.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('telegram_id', name='uq_drivers_telegram_id'),
    )
    op.create_index('ix_drivers_telegram_id', 'drivers', ['telegram_id'], unique=True)
    op.create_index('ix_drivers_brand_id', 'drivers', ['brand_id'], unique=False)
    op.create_index('ix_drivers_dispatch', 'drivers', ['status', 'is_online', 'is_available'], unique=False)

    op.create_table(
        'driver_location_trail',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('driver_id', sa.Integer(), nullable=False),
        sa.Column('latitude', sa.Float(), nullable=False),
        sa.Column('longitude', sa.Float(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['driver_id'], ['drivers.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_driver_location_trail_driver_id', 'driver_location_trail', ['driver_id'], unique=False)
    op.create_index('ix_driver_trail_driver_created', 'driver_location_trail',
                    ['driver_id', 'created_at'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_driver_trail_driver_created', table_name='driver_location_trail')
    op.drop_index('ix_driver_location_trail_driver_id', table_name='driver_location_trail')
    op.drop_table('driver_location_trail')

    op.drop_index('ix_drivers_dispatch', table_name='drivers')
    op.drop_index('ix_drivers_brand_id', table_name='drivers')
    op.drop_index('ix_drivers_telegram_id', table_name='drivers')
    op.drop_table('drivers')
