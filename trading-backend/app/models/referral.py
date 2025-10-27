"""
Referral System Models

레퍼럴 시스템
- 친구 초대 추적
- 보상 및 할인 관리
- 바이럴 성장 메트릭
"""

from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, ForeignKey, Index, Text
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta
import uuid
import secrets
import string

from app.database.base import Base


def generate_referral_code(length=8) -> str:
    """
    Generate unique referral code

    Format: TRADER_XXXXXX (uppercase alphanumeric)
    """
    chars = string.ascii_uppercase + string.digits
    code = ''.join(secrets.choice(chars) for _ in range(length))
    return f"TRADER_{code}"


class ReferralCode(Base):
    """
    사용자별 레퍼럴 코드

    각 사용자는 고유한 레퍼럴 코드를 가짐
    """
    __tablename__ = "referral_codes"

    # Primary Keys
    code = Column(String, primary_key=True)  # "TRADER_ABC12345"
    user_id = Column(String, ForeignKey("users.id"), unique=True, nullable=False)

    # Tracking
    clicks = Column(Integer, default=0)  # Total clicks on referral link
    conversions = Column(Integer, default=0)  # Actual signups
    conversion_rate = Column(Float, default=0.0)  # conversions / clicks * 100

    # Status
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime, nullable=True)  # Optional expiration

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_used_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", back_populates="referral_code")

    # Indexes
    __table_args__ = (
        Index('idx_referral_code_user', 'user_id'),
        Index('idx_referral_code_active', 'is_active'),
    )

    def __repr__(self):
        return f"<ReferralCode(code={self.code}, user_id={self.user_id}, conversions={self.conversions})>"

    def record_click(self):
        """Record a click on referral link"""
        self.clicks += 1
        self.last_used_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self._update_conversion_rate()

    def record_conversion(self):
        """Record a successful signup/conversion"""
        self.conversions += 1
        self.last_used_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self._update_conversion_rate()

    def _update_conversion_rate(self):
        """Calculate conversion rate"""
        if self.clicks > 0:
            self.conversion_rate = (self.conversions / self.clicks) * 100
        else:
            self.conversion_rate = 0.0

    def to_dict(self):
        return {
            "code": self.code,
            "user_id": self.user_id,
            "clicks": self.clicks,
            "conversions": self.conversions,
            "conversion_rate": round(self.conversion_rate, 2),
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat(),
            "last_used_at": self.last_used_at.isoformat() if self.last_used_at else None
        }


class Referral(Base):
    """
    레퍼럴 관계

    초대자(referrer) ↔ 피초대자(referred)
    """
    __tablename__ = "referrals"

    # Primary Keys
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    referrer_id = Column(String, ForeignKey("users.id"), nullable=False)  # 초대한 사람
    referred_id = Column(String, ForeignKey("users.id"), nullable=False, unique=True)  # 초대받은 사람 (한 번만 초대받을 수 있음)
    referral_code = Column(String, ForeignKey("referral_codes.code"), nullable=False)

    # Rewards
    referrer_discount_earned = Column(Float, default=0.0)  # 초대자 할인 (USDT)
    referred_discount_earned = Column(Float, default=0.0)  # 피초대자 할인 (USDT)
    referrer_share_earned = Column(Float, default=0.0)  # 초대자 수익 공유 (USDT)

    # Reward percentages
    referrer_discount_percentage = Column(Float, default=10.0)  # 초대자 거래 수수료 10% 할인
    referred_discount_percentage = Column(Float, default=10.0)  # 피초대자 거래 수수료 10% 할인
    referrer_share_percentage = Column(Float, default=5.0)  # 피초대자 수익의 5% 공유

    # Status
    status = Column(String, default="active")
    # Status: "pending" (가입만 함), "active" (첫 거래 완료), "expired" (기간 만료)

    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime, nullable=True)  # Benefit expiration date (e.g., 6 months)

    # Milestones
    first_trade_at = Column(DateTime, nullable=True)  # 피초대자 첫 거래 시각
    milestone_trades_count = Column(Integer, default=0)  # 피초대자 거래 횟수

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    referrer = relationship("User", foreign_keys=[referrer_id], backref="referrals_made")
    referred = relationship("User", foreign_keys=[referred_id], backref="referred_by")

    # Indexes
    __table_args__ = (
        Index('idx_referral_referrer', 'referrer_id'),
        Index('idx_referral_referred', 'referred_id'),
        Index('idx_referral_code', 'referral_code'),
        Index('idx_referral_status', 'status', 'is_active'),
    )

    def __repr__(self):
        return f"<Referral(referrer={self.referrer_id}, referred={self.referred_id}, status={self.status})>"

    def activate(self):
        """Activate referral when first trade is made"""
        if self.status == "pending":
            self.status = "active"
            self.first_trade_at = datetime.utcnow()
            self.updated_at = datetime.utcnow()

    def record_trade(self, trade_profit: float = 0):
        """Record a trade by referred user"""
        self.milestone_trades_count += 1

        # Calculate referrer share (5% of profit)
        if trade_profit > 0:
            share = trade_profit * (self.referrer_share_percentage / 100)
            self.referrer_share_earned += share

        self.updated_at = datetime.utcnow()

    def is_expired(self) -> bool:
        """Check if referral benefits have expired"""
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at

    def to_dict(self):
        return {
            "id": self.id,
            "referrer_id": self.referrer_id,
            "referred_id": self.referred_id,
            "referral_code": self.referral_code,
            "referrer_discount_earned": round(self.referrer_discount_earned, 2),
            "referred_discount_earned": round(self.referred_discount_earned, 2),
            "referrer_share_earned": round(self.referrer_share_earned, 2),
            "status": self.status,
            "is_active": self.is_active,
            "milestone_trades_count": self.milestone_trades_count,
            "first_trade_at": self.first_trade_at.isoformat() if self.first_trade_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "created_at": self.created_at.isoformat()
        }


class ReferralCampaign(Base):
    """
    레퍼럴 캠페인

    특별 프로모션 기간 동안 보상 증가
    예: "Summer Bonus: 20% discount instead of 10%"
    """
    __tablename__ = "referral_campaigns"

    # Primary Keys
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    # Campaign Info
    name = Column(String, nullable=False)  # "Summer Referral Bonus"
    description = Column(Text, nullable=True)
    campaign_code = Column(String, unique=True, nullable=True)  # Optional campaign-specific code

    # Bonuses
    bonus_referrer_discount = Column(Float, default=0.0)  # Additional discount % for referrer
    bonus_referred_discount = Column(Float, default=0.0)  # Additional discount % for referred
    bonus_referrer_share = Column(Float, default=0.0)  # Additional share % for referrer

    # Conditions
    min_trades_required = Column(Integer, default=1)  # Minimum trades to unlock bonus
    min_volume_required = Column(Float, default=0.0)  # Minimum trading volume (USDT)

    # Status
    is_active = Column(Boolean, default=True)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)

    # Stats
    total_participants = Column(Integer, default=0)
    total_conversions = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Indexes
    __table_args__ = (
        Index('idx_campaign_active', 'is_active', 'start_date', 'end_date'),
        Index('idx_campaign_code', 'campaign_code'),
    )

    def __repr__(self):
        return f"<ReferralCampaign(name={self.name}, active={self.is_active})>"

    def is_active_now(self) -> bool:
        """Check if campaign is currently active"""
        now = datetime.utcnow()
        return self.is_active and self.start_date <= now <= self.end_date

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "campaign_code": self.campaign_code,
            "bonus_referrer_discount": self.bonus_referrer_discount,
            "bonus_referred_discount": self.bonus_referred_discount,
            "bonus_referrer_share": self.bonus_referrer_share,
            "is_active": self.is_active,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "total_participants": self.total_participants,
            "total_conversions": self.total_conversions
        }
