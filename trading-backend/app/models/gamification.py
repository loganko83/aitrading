"""Gamification model for XP transactions"""

from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.base import Base


class XpTransaction(Base):
    """XP transaction history for gamification"""
    __tablename__ = "xp_transactions"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    amount = Column(Integer, nullable=False)  # XP change amount
    reason = Column(String, nullable=False)  # WIN, LOSS, STREAK_BONUS, BADGE_EARNED
    description = Column(String, nullable=True)
    meta_info = Column(JSON, nullable=True)  # Additional info (trade ID, badge type, etc.)
    created_at = Column(DateTime, nullable=False, server_default=func.now(), index=True)

    # Relationships
    user = relationship("User", back_populates="xp_transactions")
