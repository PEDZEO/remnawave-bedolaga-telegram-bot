"""add external_squad_uuid to tariffs

Revision ID: 0039
Revises: 0038
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = '0039'
down_revision: Union[str, None] = '0038'
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
    if _has_column('tariffs', 'external_squad_uuid'):
        op.drop_column('tariffs', 'external_squad_uuid')
