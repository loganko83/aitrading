"""User and authentication models"""

from sqlalchemy import Column, String, DateTime, Integer, Float, ARRAY, ForeignKey, Text, Boolean, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.base import Base, is_sqlite


class User(Base):
    """User model with gamification fields"""
    __tablename__ = "users"

    id = Column(String, primary_key=True)
    email = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=True)
    password = Column(String, nullable=True)
    image = Column(String, nullable=True)
    email_verified = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    # Authentication fields (JWT + 2FA)
    is_2fa_enabled = Column(Boolean, default=False, nullable=False)
    totp_secret = Column(String, nullable=True)  # Encrypted TOTP secret for 2FA
    is_active = Column(Boolean, default=True, nullable=False)

    # Notification settings
    telegram_chat_id = Column(String, nullable=True)  # Telegram chat ID for risk alerts

    # Gamification fields
    total_xp = Column(Integer, default=0)
    level = Column(Integer, default=1)
    total_trades = Column(Integer, default=0)
    total_wins = Column(Integer, default=0)
    total_losses = Column(Integer, default=0)
    total_pnl = Column(Float, default=0.0)
    win_streak = Column(Integer, default=0)
    # Use JSON for SQLite, ARRAY for PostgreSQL
    badges = Column(JSON if is_sqlite else ARRAY(String), default=[])

    # Relationships
    accounts = relationship("Account", back_populates="user", cascade="all, delete-orphan")
    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")
    api_keys = relationship("ApiKey", back_populates="user", cascade="all, delete-orphan")
    settings = relationship("TradingSettings", back_populates="user", uselist=False, cascade="all, delete-orphan")
    positions = relationship("Position", back_populates="user", cascade="all, delete-orphan")
    trades = relationship("Trade", back_populates="user", cascade="all, delete-orphan")
    webhooks = relationship("Webhook", back_populates="user", cascade="all, delete-orphan")
    xp_transactions = relationship("XpTransaction", back_populates="user", cascade="all, delete-orphan")
    strategy_configs = relationship("StrategyConfig", back_populates="user", cascade="all, delete-orphan")


class Account(Base):
    """NextAuth Account model"""
    __tablename__ = "accounts"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    type = Column(String, nullable=False)
    provider = Column(String, nullable=False)
    provider_account_id = Column(String, nullable=False)
    refresh_token = Column(Text, nullable=True)
    access_token = Column(Text, nullable=True)
    expires_at = Column(Integer, nullable=True)
    token_type = Column(String, nullable=True)
    scope = Column(String, nullable=True)
    id_token = Column(Text, nullable=True)
    session_state = Column(String, nullable=True)

    # Relationships
    user = relationship("User", back_populates="accounts")

    __table_args__ = (
        {"schema": None},
    )


class Session(Base):
    """NextAuth Session model"""
    __tablename__ = "sessions"

    id = Column(String, primary_key=True)
    session_token = Column(String, unique=True, nullable=False)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    expires = Column(DateTime, nullable=False)

    # Relationships
    user = relationship("User", back_populates="sessions")


class VerificationToken(Base):
    """NextAuth VerificationToken model"""
    __tablename__ = "verification_tokens"

    identifier = Column(String, primary_key=True)
    token = Column(String, unique=True, primary_key=True, nullable=False)
    expires = Column(DateTime, nullable=False)
