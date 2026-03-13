"""add gift system core models and tariff visibility flag

Revision ID: 0019
Revises: 0018
Create Date: 2026-03-13
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = '0019'
down_revision: Union[str, None] = '0018'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'tariffs',
        sa.Column('show_in_gift', sa.Boolean(), nullable=False, server_default=sa.text('true')),
    )

    op.create_table(
        'guest_purchases',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('token', sa.String(length=255), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('tariff_id', sa.Integer(), nullable=True),
        sa.Column('period_days', sa.Integer(), nullable=False),
        sa.Column('amount_kopeks', sa.Integer(), nullable=False),
        sa.Column('contact_type', sa.String(length=20), nullable=True),
        sa.Column('contact_value', sa.String(length=255), nullable=True),
        sa.Column('payment_method', sa.String(length=50), nullable=True),
        sa.Column('payment_id', sa.String(length=255), nullable=True),
        sa.Column('is_gift', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('buyer_user_id', sa.Integer(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('gift_recipient_type', sa.String(length=20), nullable=True),
        sa.Column('gift_recipient_value', sa.String(length=255), nullable=True),
        sa.Column('gift_message', sa.Text(), nullable=True),
        sa.Column('recipient_warning', sa.String(length=50), nullable=True),
        sa.Column('source', sa.String(length=50), nullable=False, server_default='cabinet'),
        sa.Column('subscription_url', sa.Text(), nullable=True),
        sa.Column('subscription_crypto_link', sa.Text(), nullable=True),
        sa.Column('paid_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('delivered_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['buyer_user_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['tariff_id'], ['tariffs.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('token'),
    )

    op.create_index('ix_guest_purchases_token', 'guest_purchases', ['token'])
    op.create_index('ix_guest_purchases_status', 'guest_purchases', ['status'])
    op.create_index('ix_guest_purchases_user_id', 'guest_purchases', ['user_id'])
    op.create_index('ix_guest_purchases_buyer_user_id', 'guest_purchases', ['buyer_user_id'])
    op.create_index('ix_guest_purchases_payment_id', 'guest_purchases', ['payment_id'])
    op.create_index(
        'ix_guest_purchases_user_gift_status',
        'guest_purchases',
        ['user_id', 'is_gift', 'status'],
    )

    op.alter_column('tariffs', 'show_in_gift', server_default=None)


def downgrade() -> None:
    op.drop_index('ix_guest_purchases_user_gift_status', table_name='guest_purchases')
    op.drop_index('ix_guest_purchases_payment_id', table_name='guest_purchases')
    op.drop_index('ix_guest_purchases_buyer_user_id', table_name='guest_purchases')
    op.drop_index('ix_guest_purchases_user_id', table_name='guest_purchases')
    op.drop_index('ix_guest_purchases_status', table_name='guest_purchases')
    op.drop_index('ix_guest_purchases_token', table_name='guest_purchases')
    op.drop_table('guest_purchases')
    op.drop_column('tariffs', 'show_in_gift')
