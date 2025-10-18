"""API Key model for exchange credentials"""

from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.base import Base


class ApiKey(Base):
    """Exchange API Key model (encrypted storage)"""
    __tablename__ = "api_keys"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    exchange = Column(String, default="binance", nullable=False)  # binance, okx, bybit, etc.
    api_key = Column(String, nullable=False)  # Encrypted API key
    api_secret = Column(String, nullable=False)  # Encrypted secret key
    passphrase = Column(String, nullable=True)  # Encrypted passphrase (OKX only)
    testnet = Column(Boolean, default=True)  # Testnet vs Mainnet
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="api_keys")
