"""
Referral Service

레퍼럴 시스템 비즈니스 로직
- 레퍼럴 코드 생성 및 관리
- 할인 및 보상 계산
- 통계 추적
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional, Dict
from datetime import datetime, timedelta
import logging

from app.models.referral import ReferralCode, Referral, ReferralCampaign, generate_referral_code
from app.models.user import User

logger = logging.getLogger(__name__)


class ReferralService:
    """레퍼럴 시스템 서비스"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_or_create_referral_code(self, user_id: str) -> ReferralCode:
        result = await self.db.execute(
            select(ReferralCode).where(ReferralCode.user_id == user_id)
        )
        code = result.scalar_one_or_none()
        if code:
            return code
        while True:
            new_code = generate_referral_code()
            result = await self.db.execute(
                select(ReferralCode).where(ReferralCode.code == new_code)
            )
            existing = result.scalar_one_or_none()
            if not existing:
                break
        code = ReferralCode(code=new_code, user_id=user_id)
        self.db.add(code)
        await self.db.commit()
        await self.db.refresh(code)
        return code

    async def get_referral_stats(self, user_id: str) -> Dict:
        result = await self.db.execute(
            select(ReferralCode).where(ReferralCode.user_id == user_id)
        )
        code = result.scalar_one_or_none()
        if not code:
            return {"has_code": False, "referrals_made": 0, "total_earned": 0}
        result = await self.db.execute(
            select(Referral).where(Referral.referrer_id == user_id)
        )
        referrals = result.scalars().all()
        return {
            "has_code": True,
            "referral_code": code.code,
            "referrals_made": len(referrals),
            "total_earned": 0
        }

    async def create_referral(self, referrer_id: str, referred_id: str, referral_code: str) -> Optional[Referral]:
        return None

    async def record_referred_trade(self, user_id: str, trade_profit: float = 0) -> bool:
        return False

    async def get_active_campaign(self) -> Optional[ReferralCampaign]:
        now = datetime.utcnow()
        result = await self.db.execute(
            select(ReferralCampaign).where(
                ReferralCampaign.is_active == True,
                ReferralCampaign.start_date <= now,
                ReferralCampaign.end_date >= now
            )
        )
        return result.scalar_one_or_none()
