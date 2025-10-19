"""merge_migration_heads

Revision ID: 01d0608a52af
Revises: 001_add_passphrase_testnet, 002
Create Date: 2025-10-19 19:54:45.731671

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '01d0608a52af'
down_revision: Union[str, None] = ('001_add_passphrase_testnet', '002')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
