"""
Copy Trading API Endpoints

카피 트레이딩 시스템
- 리더 팔로우/언팔로우
- 카피 설정 관리
- 통계 및 성과 조회
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select, desc
from typing import List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
import logging

from app.core.dependencies import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.models.copy_trading import CopyRelationship, CopiedTrade
from app.models.leaderboard import LeaderboardEntry
from app.services.copy_trading_executor import CopyTradingExecutor

logger = logging.getLogger(__name__)

router = APIRouter()


# ==================== Pydantic Models ====================

class StartCopyRequest(BaseModel):
    leader_id: str
    strategy_id: Optional[str] = None
    copy_ratio: float = Field(default=1.0, ge=0.1, le=2.0)
    max_position_size: Optional[float] = Field(default=None, ge=0)
    max_daily_loss: Optional[float] = None
    max_daily_trades: int = Field(default=100, ge=1, le=1000)
    profit_share_percentage: float = Field(default=10.0, ge=0, le=50)


class UpdateCopySettingsRequest(BaseModel):
    copy_ratio: Optional[float] = Field(default=None, ge=0.1, le=2.0)
    max_position_size: Optional[float] = None
    max_daily_loss: Optional[float] = None
    max_daily_trades: Optional[int] = Field(default=None, ge=1, le=1000)
    is_active: Optional[bool] = None


class CopyRelationshipResponse(BaseModel):
    id: str
    leader_id: str
    leader_name: str
    strategy_id: Optional[str]
    copy_ratio: float
    max_position_size: Optional[float]
    is_active: bool
    total_copied_trades: int
    successful_copies: int
    failed_copies: int
    total_pnl: float
    profit_share_percentage: float
    total_shared_profit: float
    created_at: str
    last_copied_at: Optional[str]

    class Config:
        from_attributes = True


# ==================== API Endpoints ====================

@router.post("/copy-trading/follow")
async def start_copying(
    request: StartCopyRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Start copying a leader's trades

    **Parameters:**
    - leader_id: User ID of the leader to copy
    - copy_ratio: 0.1 ~ 2.0 (10% ~ 200% of leader's position size)
    - max_position_size: Maximum position size in USDT
    - max_daily_loss: Maximum daily loss limit in USDT
    - profit_share_percentage: Percentage of profit to share with leader (0-50%)
    """
    try:
        # Validate leader exists
        result = await db.execute(select(User).where(User.id == request.leader_id))

        leader = result.scalar_one_or_none()
        if not leader:
            raise HTTPException(status_code=404, detail="Leader not found")

        # Cannot copy yourself
        if request.leader_id == current_user.id:
            raise HTTPException(status_code=400, detail="Cannot copy yourself")

        # Check if already following
        result = await db.execute(select(CopyRelationship).where(
            CopyRelationship.follower_id == current_user.id,
            CopyRelationship.leader_id == request.leader_id,
            CopyRelationship.is_active == True
        ))

        existing = result.scalar_one_or_none()

        if existing:
            raise HTTPException(status_code=400, detail="Already following this leader")

        # Check if leader allows copying
        result = await db.execute(select(LeaderboardEntry).where(
            LeaderboardEntry.user_id == request.leader_id,
            LeaderboardEntry.allow_copy == True,
            LeaderboardEntry.period == "monthly"
        ))

        leaderboard_entry = result.scalar_one_or_none()

        if not leaderboard_entry:
            raise HTTPException(status_code=403, detail="Leader does not allow copying")

        # Create copy relationship
        relationship = CopyRelationship(
            follower_id=current_user.id,
            leader_id=request.leader_id,
            strategy_id=request.strategy_id,
            copy_ratio=request.copy_ratio,
            max_position_size=request.max_position_size,
            max_daily_loss=request.max_daily_loss,
            max_daily_trades=request.max_daily_trades,
            profit_share_percentage=request.profit_share_percentage,
            is_active=True
        )

        db.add(relationship)
        await db.commit()
        await db.refresh(relationship)

        # Update leader's copy count
        leaderboard_entry.copy_count += 1
        await db.commit()

        logger.info(
            f"✅ Copy relationship created: {current_user.id} -> {request.leader_id} "
            f"(ratio: {request.copy_ratio})"
        )

        return {
            "success": True,
            "message": f"Started copying {leader.name}",
            "relationship_id": relationship.id,
            "copy_ratio": relationship.copy_ratio,
            "max_position_size": relationship.max_position_size
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting copy relationship: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to start copying")


@router.delete("/copy-trading/unfollow/{relationship_id}")
async def stop_copying(
    relationship_id: str,
    close_positions: bool = Query(default=False),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Stop copying a leader

    **Parameters:**
    - relationship_id: Copy relationship ID
    - close_positions: Whether to close all copied positions (default: False)
    """
    try:
        result = await db.execute(
            select(CopyRelationship).where(
                CopyRelationship.id == relationship_id,
                CopyRelationship.follower_id == current_user.id
            )
        )
        relationship = result.scalar_one_or_none()

        if not relationship:
            raise HTTPException(status_code=404, detail="Copy relationship not found")

        # Stop copying
        executor = CopyTradingExecutor(db)
        success = await executor.stop_copying(relationship_id)

        if not success:
            raise HTTPException(status_code=500, detail="Failed to stop copying")

        # Update leader's copy count
        result = await db.execute(select(LeaderboardEntry).where(
            LeaderboardEntry.user_id == relationship.leader_id,
            LeaderboardEntry.period == "monthly"
        ))

        leaderboard_entry = result.scalar_one_or_none()

        if leaderboard_entry and leaderboard_entry.copy_count > 0:
            leaderboard_entry.copy_count -= 1
            await db.commit()

        logger.info(f"🛑 Stopped copying: {relationship_id}")

        return {
            "success": True,
            "message": "Stopped copying successfully",
            "relationship_id": relationship_id,
            "positions_closed": close_positions
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error stopping copy relationship: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to stop copying")


@router.patch("/copy-trading/settings/{relationship_id}")
async def update_copy_settings(
    relationship_id: str,
    request: UpdateCopySettingsRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update copy trading settings

    Can update copy ratio, position limits, and active status
    """
    try:
        result = await db.execute(
            select(CopyRelationship).where(
                CopyRelationship.id == relationship_id,
                CopyRelationship.follower_id == current_user.id
            )
        )
        relationship = result.scalar_one_or_none()

        if not relationship:
            raise HTTPException(status_code=404, detail="Copy relationship not found")

        # Update settings
        if request.copy_ratio is not None:
            relationship.copy_ratio = request.copy_ratio
        if request.max_position_size is not None:
            relationship.max_position_size = request.max_position_size
        if request.max_daily_loss is not None:
            relationship.max_daily_loss = request.max_daily_loss
        if request.max_daily_trades is not None:
            relationship.max_daily_trades = request.max_daily_trades
        if request.is_active is not None:
            relationship.is_active = request.is_active
            if request.is_active:
                relationship.paused_at = None
            else:
                relationship.paused_at = datetime.utcnow()

        relationship.updated_at = datetime.utcnow()
        await db.commit()

        logger.info(f"⚙️ Updated copy settings: {relationship_id}")

        return {
            "success": True,
            "message": "Copy settings updated successfully",
            "relationship": relationship.to_dict()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating copy settings: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update settings")


@router.get("/copy-trading/my-leaders", response_model=List[CopyRelationshipResponse])
async def get_my_leaders(
    include_inactive: bool = Query(default=False),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get list of leaders I'm copying
    """
    try:
        query = db.query(CopyRelationship).filter(
            CopyRelationship.follower_id == current_user.id
        )

        if not include_inactive:
            query = query.filter(CopyRelationship.is_active == True)

        relationships = query.all()

        result = []
        for rel in relationships:
            leader_result = await db.execute(select(User).where(User.id == rel.leader_id))
            leader = leader_result.scalar_one_or_none()

            result.append(CopyRelationshipResponse(
                id=rel.id,
                leader_id=rel.leader_id,
                leader_name=leader.name if leader else "Unknown",
                strategy_id=rel.strategy_id,
                copy_ratio=rel.copy_ratio,
                max_position_size=rel.max_position_size,
                is_active=rel.is_active,
                total_copied_trades=rel.total_copied_trades,
                successful_copies=rel.successful_copies,
                failed_copies=rel.failed_copies,
                total_pnl=round(rel.total_pnl, 2),
                profit_share_percentage=rel.profit_share_percentage,
                total_shared_profit=round(rel.total_shared_profit, 2),
                created_at=rel.created_at.isoformat(),
                last_copied_at=rel.last_copied_at.isoformat() if rel.last_copied_at else None
            ))

        return result

    except Exception as e:
        logger.error(f"Error fetching my leaders: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch leaders")


@router.get("/copy-trading/my-followers")
async def get_my_followers(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get list of users copying me
    """
    try:
        result = await db.execute(
            select(CopyRelationship).where(
                CopyRelationship.leader_id == current_user.id,
                CopyRelationship.is_active == True
            )
        )
        relationships = result.scalars().all()

        result = []
        for rel in relationships:
            follower_result = await db.execute(select(User).where(User.id == rel.follower_id))
            follower = follower_result.scalar_one_or_none()

            result.append({
                "id": rel.id,
                "follower_id": rel.follower_id,
                "follower_name": follower.name if follower else "Unknown",
                "copy_ratio": rel.copy_ratio,
                "total_copied_trades": rel.total_copied_trades,
                "successful_copies": rel.successful_copies,
                "total_shared_profit": round(rel.total_shared_profit, 2),
                "pending_payout": round(rel.pending_payout, 2),
                "created_at": rel.created_at.isoformat(),
                "last_copied_at": rel.last_copied_at.isoformat() if rel.last_copied_at else None
            })

        return {
            "total_followers": len(result),
            "total_pending_payout": sum(rel.pending_payout for rel in relationships),
            "followers": result
        }

    except Exception as e:
        logger.error(f"Error fetching followers: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch followers")


@router.get("/copy-trading/history/{relationship_id}")
async def get_copy_history(
    relationship_id: str,
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get copy trading history for a specific relationship
    """
    try:
        # Verify ownership
        result = await db.execute(
            select(CopyRelationship).where(
                CopyRelationship.id == relationship_id,
                CopyRelationship.follower_id == current_user.id
            )
        )
        relationship = result.scalar_one_or_none()

        if not relationship:
            raise HTTPException(status_code=404, detail="Copy relationship not found")

        # Get copied trades
        copied_trades = db.query(CopiedTrade).filter(
            CopiedTrade.copy_relationship_id == relationship_id
        ).order_by(CopiedTrade.created_at.desc()).offset(offset).limit(limit).all()

        count_result = await db.execute(select(func.count()).select_from(select(CopiedTrade).where(
            CopiedTrade.copy_relationship_id == relationship_id
        ).subquery()))


        total_count = count_result.scalar()

        return {
            "relationship_id": relationship_id,
            "total_count": total_count,
            "trades": [trade.to_dict() for trade in copied_trades]
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching copy history: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch history")


@router.get("/copy-trading/stats")
async def get_copy_stats(
    period_days: int = Query(default=30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get copy trading statistics for current user

    Returns stats as both follower and leader
    """
    try:
        since = datetime.utcnow() - timedelta(days=period_days)

        # Stats as follower
        result = await db.execute(select(CopyRelationship).where(
            CopyRelationship.follower_id == current_user.id,
            CopyRelationship.created_at >= since
        ))

        follower_relationships = result.scalars().all()

        follower_stats = {
            "total_leaders_following": len(follower_relationships),
            "active_relationships": sum(1 for r in follower_relationships if r.is_active),
            "total_copied_trades": sum(r.total_copied_trades for r in follower_relationships),
            "successful_copies": sum(r.successful_copies for r in follower_relationships),
            "total_pnl": sum(r.total_pnl for r in follower_relationships),
            "total_shared_profit": sum(r.total_shared_profit for r in follower_relationships)
        }

        # Stats as leader
        result = await db.execute(select(CopyRelationship).where(
            CopyRelationship.leader_id == current_user.id,
            CopyRelationship.created_at >= since
        ))

        leader_relationships = result.scalars().all()

        leader_stats = {
            "total_followers": len(leader_relationships),
            "active_followers": sum(1 for r in leader_relationships if r.is_active),
            "total_pending_payout": sum(r.pending_payout for r in leader_relationships),
            "total_earned_from_sharing": sum(r.total_shared_profit for r in leader_relationships)
        }

        return {
            "period_days": period_days,
            "as_follower": follower_stats,
            "as_leader": leader_stats
        }

    except Exception as e:
        logger.error(f"Error fetching copy stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch stats")
