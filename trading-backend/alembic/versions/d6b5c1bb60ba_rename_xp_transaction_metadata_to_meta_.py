"""rename_xp_transaction_metadata_to_meta_info

Revision ID: d6b5c1bb60ba
Revises: ad0752fbd504
Create Date: 2025-10-19 20:02:49.268562

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd6b5c1bb60ba'
down_revision: Union[str, None] = 'ad0752fbd504'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Rename metadata column to meta_info (metadata is reserved in SQLAlchemy)"""
    op.alter_column('xp_transactions', 'metadata', new_column_name='meta_info')


def downgrade() -> None:
    """Revert meta_info column back to metadata"""
    op.alter_column('xp_transactions', 'meta_info', new_column_name='metadata')
