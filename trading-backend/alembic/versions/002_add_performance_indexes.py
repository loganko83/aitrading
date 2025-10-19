"""Add database performance indexes

Revision ID: 002
Revises: 001
Create Date: 2025-01-18 14:00:00.000000

Performance Optimizations:
- Composite indexes for frequent multi-column queries
- Partial indexes for active/open records only
- Covering indexes for common SELECT queries
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add performance indexes"""

    # =======================
    # Users Table Indexes
    # =======================

    # 1. Active users partial index (most common query)
    op.create_index(
        'idx_users_active',
        'users',
        ['is_active'],
        unique=False,
        postgresql_where=sa.text('is_active = true')
    )

    # 2. Email + active users (login queries)
    op.create_index(
        'idx_users_email_active',
        'users',
        ['email', 'is_active'],
        unique=False
    )

    # =======================
    # API Keys Table Indexes
    # =======================

    # 3. Active API keys for user (most frequent query)
    op.create_index(
        'idx_apikeys_user_active',
        'api_keys',
        ['user_id', 'is_active'],
        unique=False
    )

    # 4. Partial index for active keys only
    op.create_index(
        'idx_apikeys_active',
        'api_keys',
        ['user_id', 'exchange'],
        unique=False,
        postgresql_where=sa.text('is_active = true')
    )

    # =======================
    # Positions Table Indexes
    # =======================

    # 5. Open positions for user + symbol (real-time monitoring)
    op.create_index(
        'idx_positions_user_symbol_status',
        'positions',
        ['user_id', 'symbol', 'status'],
        unique=False
    )

    # 6. Partial index for open positions only (faster queries)
    op.create_index(
        'idx_positions_open',
        'positions',
        ['user_id', 'symbol'],
        unique=False,
        postgresql_where=sa.text("status = 'OPEN'")
    )

    # 7. Recent positions ordered by opened_at DESC
    op.create_index(
        'idx_positions_user_opened_desc',
        'positions',
        ['user_id', sa.text('opened_at DESC')],
        unique=False
    )

    # =======================
    # Trades Table Indexes
    # =======================

    # 8. Recent trades ordered by closed_at DESC (performance dashboard)
    op.create_index(
        'idx_trades_user_closed_desc',
        'trades',
        ['user_id', sa.text('closed_at DESC')],
        unique=False
    )

    # 9. Trades by symbol and time range (backtesting queries)
    op.create_index(
        'idx_trades_user_symbol_closed',
        'trades',
        ['user_id', 'symbol', 'closed_at'],
        unique=False
    )

    # 10. Covering index for PnL aggregation queries
    op.create_index(
        'idx_trades_pnl_aggregation',
        'trades',
        ['user_id', 'closed_at', 'realized_pnl'],
        unique=False
    )

    # =======================
    # Sessions Table Indexes
    # =======================

    # 11. Session token lookup (every authenticated request)
    # Note: Already has unique index on session_token, but add covering index
    op.create_index(
        'idx_sessions_token_user',
        'sessions',
        ['session_token', 'user_id'],
        unique=True
    )

    # 12. Active sessions (cleanup job)
    op.create_index(
        'idx_sessions_expires',
        'sessions',
        [sa.text('expires DESC')],
        unique=False
    )

    # =======================
    # Strategy Configs Table Indexes
    # =======================

    # 13. Active strategy configs for user
    op.create_index(
        'idx_strategy_configs_user_active',
        'strategy_configs',
        ['user_id', 'is_active'],
        unique=False
    )

    # 14. Partial index for active configs only
    op.create_index(
        'idx_strategy_configs_active',
        'strategy_configs',
        ['user_id'],
        unique=False,
        postgresql_where=sa.text('is_active = true')
    )

    # 15. Recently used configs
    op.create_index(
        'idx_strategy_configs_last_used',
        'strategy_configs',
        ['user_id', sa.text('last_used_at DESC')],
        unique=False
    )

    # =======================
    # Backtest Results Table Indexes
    # =======================

    # 16. Recent backtest results
    op.create_index(
        'idx_backtest_user_created_desc',
        'backtest_results',
        ['user_id', sa.text('created_at DESC')],
        unique=False
    )

    # 17. Backtest by symbol and strategy
    op.create_index(
        'idx_backtest_user_symbol_strategy',
        'backtest_results',
        ['user_id', 'symbol', 'strategy_id'],
        unique=False
    )

    # =======================
    # Webhooks Table Indexes
    # =======================

    # 18. Active webhooks for user
    op.create_index(
        'idx_webhooks_user_active',
        'webhooks',
        ['user_id', 'is_active'],
        unique=False
    )


def downgrade() -> None:
    """Remove performance indexes"""

    # Drop all indexes in reverse order
    op.drop_index('idx_webhooks_user_active', table_name='webhooks')
    op.drop_index('idx_backtest_user_symbol_strategy', table_name='backtest_results')
    op.drop_index('idx_backtest_user_created_desc', table_name='backtest_results')
    op.drop_index('idx_strategy_configs_last_used', table_name='strategy_configs')
    op.drop_index('idx_strategy_configs_active', table_name='strategy_configs')
    op.drop_index('idx_strategy_configs_user_active', table_name='strategy_configs')
    op.drop_index('idx_sessions_expires', table_name='sessions')
    op.drop_index('idx_sessions_token_user', table_name='sessions')
    op.drop_index('idx_trades_pnl_aggregation', table_name='trades')
    op.drop_index('idx_trades_user_symbol_closed', table_name='trades')
    op.drop_index('idx_trades_user_closed_desc', table_name='trades')
    op.drop_index('idx_positions_user_opened_desc', table_name='positions')
    op.drop_index('idx_positions_open', table_name='positions')
    op.drop_index('idx_positions_user_symbol_status', table_name='positions')
    op.drop_index('idx_apikeys_active', table_name='api_keys')
    op.drop_index('idx_apikeys_user_active', table_name='api_keys')
    op.drop_index('idx_users_email_active', table_name='users')
    op.drop_index('idx_users_active', table_name='users')
