"""
Telegram Configuration Model
사용자의 Telegram Bot 설정 저장 (암호화)
"""
from sqlalchemy import Column, String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.database.base import Base


class TelegramConfig(Base):
    __tablename__ = "telegram_configs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False, unique=True)
    
    # Encrypted fields
    bot_token = Column(String, nullable=False)  # AES-256 encrypted
    chat_id = Column(String, nullable=False)    # AES-256 encrypted
    
    # Settings
    is_active = Column(Boolean, default=True)
    notify_entry = Column(Boolean, default=True)    # 진입 알림
    notify_exit = Column(Boolean, default=True)     # 청산 알림
    notify_stop_loss = Column(Boolean, default=True)  # 손절 알림
    notify_take_profit = Column(Boolean, default=True)  # 익절 알림
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="telegram_config")


# Update User model to include telegram_config
from app.models.user import User
User.telegram_config = relationship("TelegramConfig", back_populates="user", uselist=False)
