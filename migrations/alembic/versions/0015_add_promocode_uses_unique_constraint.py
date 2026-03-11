"""add unique constraint on promocode_uses(user_id, promocode_id)

Revision ID: 0015
Revises: 0014
Create Date: 2026-03-06

Prevents race condition where concurrent requests could create
duplicate PromoCodeUse records for the same user+promocode.
"""

from typing import Sequence, Union

from alembic import op

revision: str = '0015'
down_revision: Union[str, None] = '0014'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Deduplicate any existing rows before adding constraint
    op.execute("""
        DELETE FROM promocode_uses
        WHERE id NOT IN (
            SELECT MIN(id)
            FROM promocode_uses
            GROUP BY user_id, promocode_id
        )
    """)

    # Idempotent create to avoid failures if the constraint was already added.
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM pg_constraint
                WHERE conname = 'uq_promocode_uses_user_promo'
            ) THEN
                ALTER TABLE promocode_uses
                ADD CONSTRAINT uq_promocode_uses_user_promo
                UNIQUE (user_id, promocode_id);
            END IF;
        END
        $$;
    """)


def downgrade() -> None:
    op.execute("""
        ALTER TABLE IF EXISTS promocode_uses
        DROP CONSTRAINT IF EXISTS uq_promocode_uses_user_promo
    """)
