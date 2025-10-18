"""Strategy and backtesting models"""

from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, ForeignKey, Text, ARRAY, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.base import Base


class Strategy(Base):
    """Trading strategy template (system default + user custom)"""
    __tablename__ = "strategies"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)  # "Aggressive AI Ensemble", "Conservative TA"
    description = Column(Text, nullable=False)
    category = Column(String, default="AI_ENSEMBLE", index=True)  # AI_ENSEMBLE, TECHNICAL, FUNDAMENTAL, HYBRID
    is_public = Column(Boolean, default=True, index=True)  # Public template visibility
    creator_id = Column(String, nullable=True, index=True)  # NULL = system default strategy

    # AI model weights
    ml_weight = Column(Float, default=0.40)  # 40%
    gpt4_weight = Column(Float, default=0.25)  # 25%
    claude_weight = Column(Float, default=0.25)  # 25%
    ta_weight = Column(Float, default=0.10)  # 10%

    # Entry conditions
    min_probability = Column(Float, default=0.80)  # 80% or higher
    min_confidence = Column(Float, default=0.70)  # 70% or higher
    min_agreement = Column(Float, default=0.70)  # 70% agreement

    # Risk management
    default_leverage = Column(Integer, default=3)
    position_size_pct = Column(Float, default=0.10)  # 10%
    sl_atr_multiplier = Column(Float, default=2.0)  # Stop-Loss ATR multiplier
    tp_atr_multiplier = Column(Float, default=3.0)  # Take-Profit ATR multiplier
    max_open_positions = Column(Integer, default=3)

    # Technical indicator settings
    atr_period = Column(Integer, default=14)
    rsi_period = Column(Integer, default=14)
    macd_fast = Column(Integer, default=12)
    macd_slow = Column(Integer, default=26)
    macd_signal = Column(Integer, default=9)

    # Statistics
    usage_count = Column(Integer, default=0)
    avg_win_rate = Column(Float, nullable=True)
    avg_pnl = Column(Float, nullable=True)

    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    # Relationships
    configs = relationship("StrategyConfig", back_populates="strategy", cascade="all, delete-orphan")
    backtest_results = relationship("BacktestResult", back_populates="strategy", cascade="all, delete-orphan")


class StrategyConfig(Base):
    """User-specific strategy configuration (customizes Strategy template)"""
    __tablename__ = "strategy_configs"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    strategy_id = Column(String, ForeignKey("strategies.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String, nullable=False)  # User-defined name
    is_active = Column(Boolean, default=False, index=True)

    # Custom parameters (overrides Strategy template)
    custom_params = Column(JSON, nullable=True)  # User-modified parameters

    # Execution statistics
    total_trades = Column(Integer, default=0)
    win_rate = Column(Float, nullable=True)
    total_pnl = Column(Float, default=0.0)
    max_drawdown = Column(Float, nullable=True)
    sharpe_ratio = Column(Float, nullable=True)

    # Auto-trading settings
    auto_trade_enabled = Column(Boolean, default=False)
    selected_symbols = Column(ARRAY(String), default=["BTCUSDT"])

    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    last_used_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", back_populates="strategy_configs")
    strategy = relationship("Strategy", back_populates="configs")


class BacktestResult(Base):
    """Backtesting result storage"""
    __tablename__ = "backtest_results"

    id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False, index=True)
    strategy_id = Column(String, ForeignKey("strategies.id", ondelete="CASCADE"), nullable=False, index=True)

    # Backtest settings
    symbol = Column(String, nullable=False, index=True)
    interval = Column(String, nullable=False)  # 1h, 4h, 1d
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    initial_capital = Column(Float, default=10000.0)

    # Backtest results
    total_trades = Column(Integer, nullable=False)
    winning_trades = Column(Integer, nullable=False)
    losing_trades = Column(Integer, nullable=False)
    win_rate = Column(Float, nullable=False)
    total_pnl = Column(Float, nullable=False)
    total_pnl_pct = Column(Float, nullable=False)
    max_drawdown = Column(Float, nullable=False)
    max_drawdown_pct = Column(Float, nullable=False)
    sharpe_ratio = Column(Float, nullable=True)
    sortino_ratio = Column(Float, nullable=True)
    profit_factor = Column(Float, nullable=True)
    avg_win_pnl = Column(Float, nullable=True)
    avg_loss_pnl = Column(Float, nullable=True)
    largest_win = Column(Float, nullable=True)
    largest_loss = Column(Float, nullable=True)

    # Detailed trade history (JSON array)
    trades = Column(JSON, nullable=False)  # [{entry, exit, pnl, reason}, ...]

    # Chart data (Equity Curve)
    equity_curve = Column(JSON, nullable=False)  # [{timestamp, equity}, ...]

    created_at = Column(DateTime, nullable=False, server_default=func.now(), index=True)

    # Relationships
    strategy = relationship("Strategy", back_populates="backtest_results")
