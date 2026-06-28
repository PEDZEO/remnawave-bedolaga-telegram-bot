"""add extra payment provider tables

Revision ID: 0050
Revises: 0049
Create Date: 2026-05-27
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = '0050'
down_revision: str | None = '0049'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _has_table(table_name: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return table_name in inspector.get_table_names()


def _has_column(table_name: str, column_name: str) -> bool:
    if not _has_table(table_name):
        return False

    inspector = sa.inspect(op.get_bind())
    return column_name in {column['name'] for column in inspector.get_columns(table_name)}


def _create_table_if_missing(table_name: str, *columns: sa.Column) -> None:
    if _has_table(table_name):
        return

    op.create_table(table_name, *columns)


def _drop_table_if_exists(table_name: str) -> None:
    if _has_table(table_name):
        op.drop_table(table_name)


def _payment_table(
    table_name: str,
    provider_id_column: sa.Column,
    *,
    user_nullable: bool = True,
    user_ondelete: str | None = 'SET NULL',
) -> None:
    user_fk = sa.ForeignKey('users.id', ondelete=user_ondelete) if user_ondelete else sa.ForeignKey('users.id')
    _create_table_if_missing(
        table_name,
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.Integer(), user_fk, nullable=user_nullable, index=True),
        sa.Column('order_id', sa.String(64), unique=True, nullable=False, index=True),
        provider_id_column,
        sa.Column('amount_kopeks', sa.Integer(), nullable=False),
        sa.Column('currency', sa.String(10), nullable=False, server_default='RUB'),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(32), nullable=False, server_default='pending'),
        sa.Column('is_paid', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('payment_url', sa.Text(), nullable=True),
        sa.Column('payment_method', sa.String(32), nullable=True),
        sa.Column('metadata_json', sa.JSON(), nullable=True),
        sa.Column('callback_payload', sa.JSON(), nullable=True),
        sa.Column('paid_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('transaction_id', sa.Integer(), sa.ForeignKey('transactions.id'), nullable=True),
    )


def upgrade() -> None:
    if _has_column('kassa_ai_payments', 'user_id'):
        op.alter_column('kassa_ai_payments', 'user_id', existing_type=sa.Integer(), nullable=True)

    _payment_table(
        'riopay_payments',
        sa.Column('riopay_order_id', sa.String(64), unique=True, nullable=True, index=True),
    )
    _create_table_if_missing(
        'severpay_payments',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('order_id', sa.String(64), unique=True, nullable=False, index=True),
        sa.Column('severpay_id', sa.String(64), unique=True, nullable=True, index=True),
        sa.Column('severpay_uid', sa.String(64), unique=True, nullable=True, index=True),
        sa.Column('amount_kopeks', sa.Integer(), nullable=False),
        sa.Column('currency', sa.String(10), nullable=False, server_default='RUB'),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(32), nullable=False, server_default='pending'),
        sa.Column('is_paid', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('payment_url', sa.Text(), nullable=True),
        sa.Column('payment_method', sa.String(32), nullable=True),
        sa.Column('metadata_json', sa.JSON(), nullable=True),
        sa.Column('callback_payload', sa.JSON(), nullable=True),
        sa.Column('paid_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('transaction_id', sa.Integer(), sa.ForeignKey('transactions.id'), nullable=True),
    )
    _payment_table(
        'paypear_payments',
        sa.Column('paypear_id', sa.String(64), unique=True, nullable=True, index=True),
    )
    _payment_table(
        'rollypay_payments',
        sa.Column('rollypay_payment_id', sa.String(128), unique=True, nullable=True, index=True),
    )
    _payment_table(
        'overpay_payments',
        sa.Column('overpay_payment_id', sa.String(128), unique=True, nullable=True, index=True),
    )
    _payment_table(
        'aurapay_payments',
        sa.Column('aurapay_invoice_id', sa.String(128), unique=True, nullable=True, index=True),
    )
    _payment_table(
        'etoplatezhi_payments',
        sa.Column('etoplatezhi_payment_id', sa.String(128), unique=True, nullable=True, index=True),
    )
    _payment_table(
        'antilopay_payments',
        sa.Column('antilopay_payment_id', sa.String(128), unique=True, nullable=True, index=True),
    )
    _payment_table(
        'jupiter_payments',
        sa.Column('jupiter_transaction_id', sa.String(128), unique=True, nullable=True, index=True),
    )
    _payment_table(
        'donut_payments',
        sa.Column('donut_transaction_id', sa.String(128), unique=True, nullable=True, index=True),
    )
    _payment_table(
        'lava_payments',
        sa.Column('lava_invoice_id', sa.String(128), unique=True, nullable=True, index=True),
    )


def downgrade() -> None:
    for table_name in (
        'lava_payments',
        'donut_payments',
        'jupiter_payments',
        'antilopay_payments',
        'etoplatezhi_payments',
        'aurapay_payments',
        'overpay_payments',
        'rollypay_payments',
        'paypear_payments',
        'severpay_payments',
        'riopay_payments',
    ):
        _drop_table_if_exists(table_name)

    if _has_column('kassa_ai_payments', 'user_id'):
        op.alter_column('kassa_ai_payments', 'user_id', existing_type=sa.Integer(), nullable=False)
