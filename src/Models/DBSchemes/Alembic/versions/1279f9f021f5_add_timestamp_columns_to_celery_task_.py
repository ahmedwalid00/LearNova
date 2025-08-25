"""add_timestamp_columns_to_celery_task_executions

Revision ID: 1279f9f021f5
Revises: 9b3f6a2c4d1e
Create Date: 2025-08-25 03:29:41.391071

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '1279f9f021f5'
down_revision: Union[str, None] = '9b3f6a2c4d1e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add missing timestamp columns to celery_task_executions table
    op.add_column('celery_task_executions', sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True))
    op.add_column('celery_task_executions', sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('celery_task_executions', sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    # Remove the added timestamp columns
    op.drop_column('celery_task_executions', 'deleted_at')
    op.drop_column('celery_task_executions', 'updated_at')
    op.drop_column('celery_task_executions', 'created_at')
