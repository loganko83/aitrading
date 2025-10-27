from sqlalchemy import Column, String, Float, Boolean, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.database.base import Base


class InvestmentType(str, enum.Enum):
    PERCENTAGE = "percentage"
    FIXED = "fixed"


class TradingConfig(Base):
    __tablename__ = "trading_configs"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    api_key_id = Column(String, ForeignKey("api_keys.id"), nullable=False)
    
    # Strategy settings
    strategy = Column(String, nullable=True)  # 전략 이름 (optional)
    
    # Investment settings
    investment_type = Column(Enum(InvestmentType), default=InvestmentType.PERCENTAGE)
    investment_value = Column(Float, nullable=False)  # 0.1 = 10% or 100 = 100 USDT
    
    # Risk management
    leverage = Column(Float, default=10.0)
    stop_loss_percentage = Column(Float, default=2.0)  # 2% stop loss
    take_profit_percentage = Column(Float, default=5.0)  # 5% take profit
    
    # Activation
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="trading_configs")
    api_key = relationship("ApiKey", back_populates="trading_configs")
