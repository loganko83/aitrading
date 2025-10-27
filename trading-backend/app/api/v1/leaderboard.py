"""
Leaderboard API Endpoints - Async Version
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
from typing import List, Optional
from datetime import datetime
import logging

from app.core.dependencies import get_db
from app.core.auth import get_current_user, get_current_user_optional
from app.models.user import User
from app.models.leaderboard import LeaderboardEntry, LeaderboardBadge
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter()


class LeaderboardEntryResponse(BaseModel):
    id: str
    user_id: str
    username: str
    strategy_id: Optional[str]
    strategy_name: Optional[str]
    rank: Optional[int]
    rank_change: int
    win_rate: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    total_pnl: float
    roi: float
    sharpe_ratio: float
    max_drawdown: float
    profit_factor: float
    copy_count: int
    allow_copy: bool
    period: str
    last_trade_at: Optional[str]
    updated_at: str
    badges: List[dict] = []


class LeaderboardResponse(BaseModel):
    period: str
    total_count: int
    page: int
    page_size: int
    entries: List[LeaderboardEntryResponse]


@router.get("/leaderboard")
async def get_leaderboard(
    period: str = Query("monthly"),
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=500),
    sort_by: str = Query("roi"),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    try:
        query = select(LeaderboardEntry).where(LeaderboardEntry.period == period)
        
        if not current_user:
            query = query.where(LeaderboardEntry.is_public == True)
        
        if sort_by == "roi":
            query = query.order_by(desc(LeaderboardEntry.roi))
        elif sort_by == "win_rate":
            query = query.order_by(desc(LeaderboardEntry.win_rate))
        
        count_query = select(func.count()).select_from(query.subquery())
        count_result = await db.execute(count_query)
        total_count = count_result.scalar() or 0
        
        offset = (page - 1) * page_size
        result = await db.execute(query.offset(offset).limit(page_size))
        entries = result.scalars().all()
        
        response_entries = []
        for entry in entries:
            user_query = select(User).where(User.id == entry.user_id)
            user_result = await db.execute(user_query)
            user = user_result.scalar_one_or_none()
            
            badges_query = select(LeaderboardBadge).where(
                LeaderboardBadge.user_id == entry.user_id,
                LeaderboardBadge.is_active == True
            )
            badges_result = await db.execute(badges_query)
            badges = badges_result.scalars().all()
            
            response_entries.append(LeaderboardEntryResponse(
                id=entry.id,
                user_id=entry.user_id,
                username=user.name if user else "Unknown",
                strategy_id=entry.strategy_id,
                strategy_name=None,
                rank=entry.rank,
                rank_change=entry.rank_change,
                win_rate=round(entry.win_rate, 2),
                total_trades=entry.total_trades,
                winning_trades=entry.winning_trades,
                losing_trades=entry.losing_trades,
                total_pnl=round(entry.total_pnl, 2),
                roi=round(entry.roi, 2),
                sharpe_ratio=round(entry.sharpe_ratio, 2),
                max_drawdown=round(entry.max_drawdown, 2),
                profit_factor=round(entry.profit_factor, 2),
                copy_count=entry.copy_count,
                allow_copy=entry.allow_copy,
                period=entry.period,
                last_trade_at=entry.last_trade_at.isoformat() if entry.last_trade_at else None,
                updated_at=entry.updated_at.isoformat(),
                badges=[{"name": b.badge_type, "icon": b.icon_url} for b in badges]
            ))
        
        return {
            "period": period,
            "total_count": total_count,
            "page": page,
            "page_size": page_size,
            "entries": response_entries
        }
    
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail="Failed to fetch leaderboard")
