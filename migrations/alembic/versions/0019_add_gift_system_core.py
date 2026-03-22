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


def _has_column(table: str, column: str) -> bool:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    return column in [c['name'] for c in inspector.get_columns(table)]


def _has_table(table: str) -> bool:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    return inspector.has_table(table)


def _has_index(table: str, index_name: str) -> bool:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    return index_name in [index['name'] for index in inspector.get_indexes(table)]


def upgrade() -> None:
    if not _has_column('tariffs', 'show_in_gift'):
        op.add_column(
            'tariffs',
            sa.Column('show_in_gift', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        )

    if not _has_table('guest_purchases'):
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

    if not _has_index('guest_purchases', 'ix_guest_purchases_token'):
        op.create_index('ix_guest_purchases_token', 'guest_purchases', ['token'])
    if not _has_index('guest_purchases', 'ix_guest_purchases_status'):
        op.create_index('ix_guest_purchases_status', 'guest_purchases', ['status'])
    if not _has_index('guest_purchases', 'ix_guest_purchases_user_id'):
        op.create_index('ix_guest_purchases_user_id', 'guest_purchases', ['user_id'])
    if not _has_index('guest_purchases', 'ix_guest_purchases_buyer_user_id'):
        op.create_index('ix_guest_purchases_buyer_user_id', 'guest_purchases', ['buyer_user_id'])
    if not _has_index('guest_purchases', 'ix_guest_purchases_payment_id'):
        op.create_index('ix_guest_purchases_payment_id', 'guest_purchases', ['payment_id'])
    if not _has_index('guest_purchases', 'ix_guest_purchases_user_gift_status'):
        op.create_index(
            'ix_guest_purchases_user_gift_status',
            'guest_purchases',
            ['user_id', 'is_gift', 'status'],
        )

    if _has_column('tariffs', 'show_in_gift'):
        op.alter_column('tariffs', 'show_in_gift', server_default=None)


def downgrade() -> None:
    op.drop_index('ix_guest_purchases_user_gift_status', table_name='guest_purchases')
    op.drop_index('ix_guest_purchases_payment_id', table_name='guest_purchases')
    op.drop_index('ix_guest_purchases_buyer_user_id', table_name='guest_purchases')
    op.drop_index('ix_guest_purchases_user_id', table_name='guest_purchases')
    op.drop_index('ix_guest_purchases_status', table_name='guest_purchases')
    op.drop_index('ix_guest_purchases_token', table_name='guest_purchases')
    op.drop_table('guest_purchases')
    if _has_column('tariffs', 'show_in_gift'):
        op.drop_column('tariffs', 'show_in_gift')
