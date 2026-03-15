"""repair missing external_squad_uuid on tariffs

Revision ID: 0040
Revises: 0039
Create Date: 2026-03-15

Some databases may already be stamped at revision 0039 while still missing
the ``tariffs.external_squad_uuid`` column. This repair migration re-checks
the schema and adds the column if needed.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = '0040'
down_revision: Union[str, None] = '0039'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_column(table: str, column: str) -> bool:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    return column in [c['name'] for c in inspector.get_columns(table)]


def upgrade() -> None:
    if not _has_column('tariffs', 'external_squad_uuid'):
        op.add_column(
            'tariffs',
            sa.Column('external_squad_uuid', sa.String(length=36), nullable=True),
        )


def downgrade() -> None:
    # Repair migration: downgrade is intentionally a no-op.
    pass
