"""Trading-related models (Settings, Positions, Trades)"""

from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, ForeignKey, ARRAY, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.base import Base, is_sqlite


class TradingSettings(Base):
    """User trading settings"""
    __tablename__ = "trading_settings"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    risk_tolerance = Column(String, default="medium")  # low, medium, high
    # Use JSON for SQLite, ARRAY for PostgreSQL
    selected_coins = Column(JSON if is_sqlite else ARRAY(String), default=["BTC/USDT"])
    leverage = Column(Integer, default=3)
    position_size_pct = Column(Float, default=0.10)  # 10%
    stop_loss_atr_multiplier = Column(Float, default=2.0)
    take_profit_atr_multiplier = Column(Float, default=3.0)
    auto_close_on_reversal = Column(Boolean, default=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="settings")


class Position(Base):
    """Open trading positions"""
    __tablename__ = "positions"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    symbol = Column(String, nullable=False, index=True)  # BTC/USDT
    side = Column(String, nullable=False)  # LONG, SHORT
    quantity = Column(Float, nullable=False)
    entry_price = Column(Float, nullable=False)
    current_price = Column(Float, nullable=False)
    stop_loss = Column(Float, nullable=False)
    take_profit = Column(Float, nullable=False)
    leverage = Column(Integer, nullable=False)
    unrealized_pnl = Column(Float, nullable=False)
    status = Column(String, default="OPEN", index=True)  # OPEN, CLOSED
    ai_confidence = Column(Float, nullable=True)  # 0.0-1.0
    ai_reason = Column(Text, nullable=True)  # AI decision reasoning
    opened_at = Column(DateTime, nullable=False, server_default=func.now())
    closed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="positions")


class Trade(Base):
    """Completed trade history"""
    __tablename__ = "trades"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    symbol = Column(String, nullable=False, index=True)
    side = Column(String, nullable=False)  # LONG, SHORT
    quantity = Column(Float, nullable=False)
    entry_price = Column(Float, nullable=False)
    exit_price = Column(Float, nullable=False)
    stop_loss = Column(Float, nullable=False)
    take_profit = Column(Float, nullable=False)
    leverage = Column(Integer, nullable=False)
    realized_pnl = Column(Float, nullable=False)
    pnl_percent = Column(Float, nullable=False)
    ai_confidence = Column(Float, nullable=True)
    ai_reason = Column(Text, nullable=True)
    exit_reason = Column(String, nullable=True)  # TP_HIT, SL_HIT, REVERSAL, MANUAL
    opened_at = Column(DateTime, nullable=False)
    closed_at = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="trades")
