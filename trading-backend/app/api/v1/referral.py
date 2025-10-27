"""
Referral API Endpoints

레퍼럴 시스템
- 레퍼럴 코드 조회/생성
- 친구 초대 추적
- 보상 및 통계
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select
from typing import List
from pydantic import BaseModel
import logging

from app.core.dependencies import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.models.referral import Referral, ReferralCode
from app.services.referral_service import ReferralService

logger = logging.getLogger(__name__)

router = APIRouter()


# ==================== Pydantic Models ====================

class ReferralCodeResponse(BaseModel):
    code: str
    clicks: int
    conversions: int
    conversion_rate: float
    share_url: str
    created_at: str


class ReferralResponse(BaseModel):
    id: str
    referred_user_name: str
    referral_code: str
    status: str
    is_active: bool
    milestone_trades_count: int
    referrer_share_earned: float
    created_at: str
    first_trade_at: str = None


# ==================== API Endpoints ====================

@router.get("/referral/my-code", response_model=ReferralCodeResponse)
async def get_my_referral_code(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get my referral code (creates one if doesn't exist)
    """
    try:
        service = ReferralService(db)
        code = await service.get_or_create_referral_code(current_user.id)

        # Generate share URL
        base_url = "https://trendy.storydot.kr"
        share_url = f"{base_url}/signup?ref={code.code}"

        return ReferralCodeResponse(
            code=code.code,
            clicks=code.clicks,
            conversions=code.conversions,
            conversion_rate=round(code.conversion_rate, 2),
            share_url=share_url,
            created_at=code.created_at.isoformat()
        )

    except Exception as e:
        logger.error(f"Error getting referral code: {e}")
        raise HTTPException(status_code=500, detail="Failed to get referral code")


@router.get("/referral/stats")
async def get_referral_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get referral statistics for current user
    """
    try:
        service = ReferralService(db)
        stats = await service.get_referral_stats(current_user.id)

        return stats

    except Exception as e:
        logger.error(f"Error getting referral stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get stats")


@router.get("/referral/my-referrals")
async def get_my_referrals(
    include_inactive: bool = Query(default=False),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get list of users I've referred
    """
    try:
        query = select(Referral).where(Referral.referrer_id == current_user.id)

        if not include_inactive:
            query = query.where(Referral.is_active == True)

        result = await db.execute(query)
        referrals = result.scalars().all()

        result = []
        for ref in referrals:
            ref_result = await db.execute(select(User).where(User.id == ref.referred_id))
            referred_user = ref_result.scalar_one_or_none()

            result.append({
                "id": ref.id,
                "referred_user_id": ref.referred_id,
                "referred_user_name": referred_user.name if referred_user else "Unknown",
                "referral_code": ref.referral_code,
                "status": ref.status,
                "is_active": ref.is_active,
                "milestone_trades_count": ref.milestone_trades_count,
                "referrer_share_earned": round(ref.referrer_share_earned, 2),
                "referrer_discount_earned": round(ref.referrer_discount_earned, 2),
                "created_at": ref.created_at.isoformat(),
                "first_trade_at": ref.first_trade_at.isoformat() if ref.first_trade_at else None
            })

        return {
            "total_referrals": len(result),
            "active_referrals": sum(1 for r in result if r["is_active"]),
            "total_earned": sum(r["referrer_share_earned"] for r in result),
            "referrals": result
        }

    except Exception as e:
        logger.error(f"Error getting referrals: {e}")
        raise HTTPException(status_code=500, detail="Failed to get referrals")


@router.post("/referral/track-click/{code}")
async def track_referral_click(
    code: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Track a click on referral link (public endpoint)

    Called when someone clicks a referral link
    """
    try:
        result = await db.execute(
            select(ReferralCode).where(
                ReferralCode.code == code,
                ReferralCode.is_active == True
            )
        )
        ref_code = result.scalar_one_or_none()

        if not ref_code:
            raise HTTPException(status_code=404, detail="Referral code not found")

        ref_code.record_click()
        await db.commit()

        return {
            "success": True,
            "message": "Click tracked"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error tracking click: {e}")
        raise HTTPException(status_code=500, detail="Failed to track click")


@router.get("/referral/campaigns")
async def get_active_campaigns(
    db: AsyncSession = Depends(get_db)
):
    """
    Get active referral campaigns (public endpoint)
    """
    try:
        service = ReferralService(db)
        campaign = await service.get_active_campaign()

        if not campaign:
            return {"active_campaign": None}

        return {
            "active_campaign": campaign.to_dict()
        }

    except Exception as e:
        logger.error(f"Error getting campaigns: {e}")
        raise HTTPException(status_code=500, detail="Failed to get campaigns")
