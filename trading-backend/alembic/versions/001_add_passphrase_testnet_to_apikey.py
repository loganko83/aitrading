"""Add passphrase and testnet to ApiKey model

Revision ID: 001_add_passphrase_testnet
Revises:
Create Date: 2025-01-18 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '001_add_passphrase_testnet'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add passphrase (for OKX) and testnet columns to api_keys table"""

    # Add passphrase column (nullable, encrypted)
    op.add_column('api_keys', sa.Column('passphrase', sa.String(), nullable=True))

    # Add testnet column (default True for safety)
    op.add_column('api_keys', sa.Column('testnet', sa.Boolean(), nullable=False, server_default='true'))


def downgrade() -> None:
    """Remove passphrase and testnet columns from api_keys table"""

    op.drop_column('api_keys', 'testnet')
    op.drop_column('api_keys', 'passphrase')
