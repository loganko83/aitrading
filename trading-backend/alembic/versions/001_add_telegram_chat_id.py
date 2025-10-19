"""Add telegram_chat_id to users table

Revision ID: 001
Revises:
Create Date: 2025-01-18 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add telegram_chat_id column to users table"""
    op.add_column(
        'users',
        sa.Column('telegram_chat_id', sa.String(), nullable=True)
    )


def downgrade() -> None:
    """Remove telegram_chat_id column from users table"""
    op.drop_column('users', 'telegram_chat_id')
