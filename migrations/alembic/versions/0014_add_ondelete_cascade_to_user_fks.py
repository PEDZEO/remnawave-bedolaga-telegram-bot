"""add ondelete CASCADE/SET NULL to FK constraints referencing users.id

Revision ID: 0014
Revises: 0013
Create Date: 2026-03-06

This is an adapted migration for our branch graph.
It safely:
1. Cleans orphan records in child tables (DELETE or SET NULL)
2. Recreates selected FK constraints with ON DELETE behavior
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = '0014'
down_revision: Union[str, None] = '0013'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# (table, column, ondelete, fk_name)
_FK_CHANGES: list[tuple[str, str, str, str]] = [
    ('yookassa_payments', 'user_id', 'CASCADE', 'yookassa_payments_user_id_fkey'),
    ('cryptobot_payments', 'user_id', 'CASCADE', 'cryptobot_payments_user_id_fkey'),
    ('heleket_payments', 'user_id', 'CASCADE', 'heleket_payments_user_id_fkey'),
    ('mulenpay_payments', 'user_id', 'CASCADE', 'mulenpay_payments_user_id_fkey'),
    ('pal24_payments', 'user_id', 'CASCADE', 'pal24_payments_user_id_fkey'),
    ('wata_payments', 'user_id', 'CASCADE', 'wata_payments_user_id_fkey'),
    ('platega_payments', 'user_id', 'CASCADE', 'platega_payments_user_id_fkey'),
    ('cloudpayments_payments', 'user_id', 'CASCADE', 'cloudpayments_payments_user_id_fkey'),
    ('freekassa_payments', 'user_id', 'CASCADE', 'freekassa_payments_user_id_fkey'),
    ('kassa_ai_payments', 'user_id', 'CASCADE', 'kassa_ai_payments_user_id_fkey'),
    ('users', 'referred_by_id', 'SET NULL', 'users_referred_by_id_fkey'),
    ('subscriptions', 'user_id', 'CASCADE', 'subscriptions_user_id_fkey'),
    ('transactions', 'user_id', 'CASCADE', 'transactions_user_id_fkey'),
    ('subscription_conversions', 'user_id', 'CASCADE', 'subscription_conversions_user_id_fkey'),
    ('promocodes', 'created_by', 'SET NULL', 'promocodes_created_by_fkey'),
    ('promocode_uses', 'user_id', 'CASCADE', 'promocode_uses_user_id_fkey'),
    ('referral_earnings', 'user_id', 'CASCADE', 'referral_earnings_user_id_fkey'),
    ('referral_earnings', 'referral_id', 'CASCADE', 'referral_earnings_referral_id_fkey'),
    ('withdrawal_requests', 'user_id', 'CASCADE', 'withdrawal_requests_user_id_fkey'),
    ('withdrawal_requests', 'processed_by', 'SET NULL', 'withdrawal_requests_processed_by_fkey'),
    ('broadcast_history', 'admin_id', 'CASCADE', 'broadcast_history_admin_id_fkey'),
    ('welcome_texts', 'created_by', 'SET NULL', 'welcome_texts_created_by_fkey'),
    ('advertising_campaigns', 'created_by', 'SET NULL', 'advertising_campaigns_created_by_fkey'),
    ('admin_roles', 'created_by', 'SET NULL', 'admin_roles_created_by_fkey'),
    ('user_roles', 'assigned_by', 'SET NULL', 'user_roles_assigned_by_fkey'),
    ('access_policies', 'created_by', 'SET NULL', 'access_policies_created_by_fkey'),
    ('admin_audit_log', 'user_id', 'CASCADE', 'admin_audit_log_user_id_fkey'),
]

# (table, column, nullable)
_ALL_USER_FKS: list[tuple[str, str, bool]] = [
    ('yookassa_payments', 'user_id', False),
    ('cryptobot_payments', 'user_id', False),
    ('heleket_payments', 'user_id', False),
    ('mulenpay_payments', 'user_id', False),
    ('pal24_payments', 'user_id', False),
    ('wata_payments', 'user_id', False),
    ('platega_payments', 'user_id', False),
    ('cloudpayments_payments', 'user_id', False),
    ('freekassa_payments', 'user_id', False),
    ('kassa_ai_payments', 'user_id', False),
    ('user_promo_groups', 'user_id', False),
    ('subscriptions', 'user_id', False),
    ('transactions', 'user_id', False),
    ('subscription_conversions', 'user_id', False),
    ('promocode_uses', 'user_id', False),
    ('referral_earnings', 'user_id', False),
    ('referral_earnings', 'referral_id', False),
    ('withdrawal_requests', 'user_id', False),
    ('partner_applications', 'user_id', False),
    ('referral_contest_events', 'referrer_id', False),
    ('referral_contest_events', 'referral_id', False),
    ('contest_attempts', 'user_id', False),
    ('sent_notifications', 'user_id', False),
    ('subscription_events', 'user_id', False),
    ('discount_offers', 'user_id', False),
    ('broadcast_history', 'admin_id', False),
    ('poll_responses', 'user_id', False),
    ('advertising_campaign_registrations', 'user_id', False),
    ('tickets', 'user_id', False),
    ('ticket_messages', 'user_id', False),
    ('ticket_notifications', 'user_id', False),
    ('cabinet_refresh_tokens', 'user_id', False),
    ('wheel_spins', 'user_id', False),
    ('user_roles', 'user_id', False),
    ('admin_audit_log', 'user_id', False),
    ('users', 'referred_by_id', True),
    ('promocodes', 'created_by', True),
    ('withdrawal_requests', 'processed_by', True),
    ('promo_offer_templates', 'created_by', True),
    ('promo_offer_logs', 'user_id', True),
    ('polls', 'created_by', True),
    ('support_audit_logs', 'actor_user_id', True),
    ('support_audit_logs', 'target_user_id', True),
    ('user_messages', 'created_by', True),
    ('welcome_texts', 'created_by', True),
    ('pinned_messages', 'created_by', True),
    ('advertising_campaigns', 'partner_user_id', True),
    ('advertising_campaigns', 'created_by', True),
    ('button_click_logs', 'user_id', True),
    ('referral_contests', 'created_by', True),
    ('admin_roles', 'created_by', True),
    ('user_roles', 'assigned_by', True),
    ('access_policies', 'created_by', True),
    ('partner_applications', 'processed_by', True),
]


def _inspector() -> sa.Inspector:
    return sa.inspect(op.get_bind())


def _has_table(table_name: str) -> bool:
    return table_name in _inspector().get_table_names()


def _has_column(table_name: str, column_name: str) -> bool:
    if not _has_table(table_name):
        return False
    return column_name in [column['name'] for column in _inspector().get_columns(table_name)]


def _has_fk(table_name: str, fk_name: str) -> bool:
    if not _has_table(table_name):
        return False
    return any(fk.get('name') == fk_name for fk in _inspector().get_foreign_keys(table_name))


def upgrade() -> None:
    # Step 1: clean orphan links before FK recreation
    for table, column, nullable in _ALL_USER_FKS:
        if not _has_column(table, column):
            continue
        if nullable:
            op.execute(
                sa.text(
                    f'UPDATE {table} SET {column} = NULL '
                    f'WHERE {column} IS NOT NULL AND {column} NOT IN (SELECT id FROM users)'
                )
            )
        else:
            op.execute(sa.text(f'DELETE FROM {table} WHERE {column} NOT IN (SELECT id FROM users)'))

    # Step 2: recreate target constraints with desired ondelete
    for table, column, ondelete, fk_name in _FK_CHANGES:
        if not _has_column(table, column):
            continue
        if _has_fk(table, fk_name):
            op.drop_constraint(fk_name, table, type_='foreignkey')
        op.create_foreign_key(fk_name, table, 'users', [column], ['id'], ondelete=ondelete)


def downgrade() -> None:
    for table, column, _ondelete, fk_name in _FK_CHANGES:
        if not _has_column(table, column):
            continue
        if _has_fk(table, fk_name):
            op.drop_constraint(fk_name, table, type_='foreignkey')
        op.create_foreign_key(fk_name, table, 'users', [column], ['id'])
