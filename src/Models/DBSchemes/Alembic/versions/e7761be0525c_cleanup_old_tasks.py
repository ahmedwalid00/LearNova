"""Cleanup old tasks

Revision ID: e7761be0525c
Revises: 608c08e59c3d
Create Date: 2025-08-24 04:35:49.017562

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e7761be0525c'
down_revision: Union[str, None] = '608c08e59c3d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Migration adjusted to NO-OP to avoid unsafe type casting on student_id.
    # Original migration attempted to change student_id UUID -> INTEGER which
    # is unsafe because values cannot be coerced. We'll skip this step.
    print('Skipping unsafe migration: e7761be0525c_cleanup_old_tasks (no-op)')
    pass
    # ### end Alembic commands ###


def downgrade() -> None:
    # No-op downgrade for skipped migration.
    print('Skipping downgrade for e7761be0525c_cleanup_old_tasks (no-op)')
    pass
    # ### end Alembic commands ###
