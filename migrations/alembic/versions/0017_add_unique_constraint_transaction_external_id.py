"""add unique constraint on transactions(external_id, payment_method)

Revision ID: 0017
Revises: 0016
Create Date: 2026-03-06

Prevents duplicate transaction records for the same payment provider
external ID, which could cause double-crediting of user balance.
NULL external_id values do not violate the constraint in PostgreSQL.
"""

from typing import Sequence, Union

from alembic import op

revision: str = '0017'
down_revision: Union[str, None] = '0015'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Deduplicate any existing rows with same (external_id, payment_method)
    # where external_id is not NULL. Keep the row with the lowest id,
    # suffix duplicates with _dup_{id} to preserve audit trail.
    op.execute("""
        UPDATE transactions
        SET external_id = external_id || '_dup_' || id::text
        WHERE external_id IS NOT NULL
          AND id NOT IN (
              SELECT MIN(id)
              FROM transactions
              WHERE external_id IS NOT NULL
              GROUP BY external_id, payment_method
          )
    """)

    # Idempotent create to avoid failures if the constraint was already added.
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM pg_constraint
                WHERE conname = 'uq_transaction_external_id_method'
            ) THEN
                ALTER TABLE transactions
                ADD CONSTRAINT uq_transaction_external_id_method
                UNIQUE (external_id, payment_method);
            END IF;
        END
        $$;
    """)


def downgrade() -> None:
    op.execute("""
        ALTER TABLE IF EXISTS transactions
        DROP CONSTRAINT IF EXISTS uq_transaction_external_id_method
    """)
