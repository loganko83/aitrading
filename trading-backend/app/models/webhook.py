"""Webhook model for TradingView integration"""

from sqlalchemy import Column, String, Boolean, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.base import Base


class Webhook(Base):
    """TradingView Webhook configuration"""
    __tablename__ = "webhooks"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    webhook_url = Column(String, unique=True, nullable=False, index=True)
    secret_token = Column(String, nullable=False)  # HMAC-SHA256 signature verification
    is_active = Column(Boolean, default=True)
    total_triggers = Column(Integer, default=0)
    last_triggered = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="webhooks")
