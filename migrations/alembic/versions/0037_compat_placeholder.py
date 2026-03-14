"""compat placeholder for missing 0037 revision

Revision ID: 0037
Revises: 0018

This migration intentionally does nothing and exists only to keep
upgrade path continuity for environments that already have DB stamped
or migrated to 0037 from previous builds.
"""

from typing import Sequence, Union


revision: str = '0037'
down_revision: Union[str, None] = '0018'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
