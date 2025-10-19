"""add_composite_indexes_for_performance

Revision ID: ad0752fbd504
Revises: 01d0608a52af
Create Date: 2025-10-19 19:54:57.035180

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ad0752fbd504'
down_revision: Union[str, None] = '01d0608a52af'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add composite indexes for common query patterns"""

    # 1. Positions: Optimize "Get all OPEN positions for user X"
    op.create_index(
        'ix_positions_user_status',
        'positions',
        ['user_id', 'status'],
        unique=False
    )

    # 2. Trades: Optimize "Get user's recent trades sorted by date"
    op.create_index(
        'ix_trades_user_closed_at',
        'trades',
        ['user_id', 'closed_at'],
        unique=False
    )

    # 3. API Keys: Optimize "Get active API key for user+exchange"
    op.create_index(
        'ix_api_keys_user_exchange_active',
        'api_keys',
        ['user_id', 'exchange', 'is_active'],
        unique=False
    )

    # 4. Strategy Configs: Optimize "Get active strategy for user"
    op.create_index(
        'ix_strategy_configs_user_active',
        'strategy_configs',
        ['user_id', 'is_active'],
        unique=False
    )

    # 5. Sessions: Optimize session validation queries
    op.create_index(
        'ix_sessions_user_expires',
        'sessions',
        ['user_id', 'expires'],
        unique=False
    )

    # 6. Positions: Optimize symbol-based queries
    op.create_index(
        'ix_positions_symbol_status',
        'positions',
        ['symbol', 'status'],
        unique=False
    )

    # 7. XP Transactions: Optimize user activity timeline
    op.create_index(
        'ix_xp_transactions_user_created_at',
        'xp_transactions',
        ['user_id', 'created_at'],
        unique=False
    )


def downgrade() -> None:
    """Remove composite indexes"""

    op.drop_index('ix_xp_transactions_user_created_at', table_name='xp_transactions')
    op.drop_index('ix_positions_symbol_status', table_name='positions')
    op.drop_index('ix_sessions_user_expires', table_name='sessions')
    op.drop_index('ix_strategy_configs_user_active', table_name='strategy_configs')
    op.drop_index('ix_api_keys_user_exchange_active', table_name='api_keys')
    op.drop_index('ix_trades_user_closed_at', table_name='trades')
    op.drop_index('ix_positions_user_status', table_name='positions')
