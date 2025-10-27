"""
Leaderboard Calculator Service

실시간 리더보드 랭킹 계산 및 업데이트
"""

from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from datetime import datetime, timedelta
from typing import List, Optional, Dict
import logging

from app.models.leaderboard import LeaderboardEntry
from app.models.user import User
from app.models.trading import Trade

logger = logging.getLogger(__name__)


class LeaderboardCalculator:
    """리더보드 계산 및 업데이트 서비스"""

    def __init__(self, db: Session):
        self.db = db

    def calculate_period_dates(self, period: str) -> tuple:
        """
        기간별 시작/종료 날짜 계산

        Args:
            period: "daily", "weekly", "monthly", "all_time"

        Returns:
            (period_start, period_end) tuple
        """
        now = datetime.utcnow()

        if period == "daily":
            start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end = start + timedelta(days=1)
        elif period == "weekly":
            # 월요일부터 시작
            start = now - timedelta(days=now.weekday())
            start = start.replace(hour=0, minute=0, second=0, microsecond=0)
            end = start + timedelta(days=7)
        elif period == "monthly":
            start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            # 다음달 1일
            if now.month == 12:
                end = start.replace(year=now.year + 1, month=1)
            else:
                end = start.replace(month=now.month + 1)
        else:  # all_time
            start = datetime(2020, 1, 1)  # 서비스 시작일
            end = datetime(2099, 12, 31)

        return start, end

    async def calculate_user_performance(
        self,
        user_id: str,
        period_start: datetime,
        period_end: datetime
    ) -> Dict:
        """
        특정 사용자의 기간별 성과 계산

        Returns:
            성과 지표 딕셔너리
        """
        # 기간 내 거래 조회
        trades = self.db.query(Trade).filter(
            and_(
                Trade.user_id == user_id,
                Trade.created_at >= period_start,
                Trade.created_at < period_end
            )
        ).all()

        if not trades:
            return None

        # 성과 계산
        total_trades = len(trades)
        winning_trades = sum(1 for t in trades if t.pnl and t.pnl > 0)
        losing_trades = sum(1 for t in trades if t.pnl and t.pnl <= 0)
        
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        
        total_pnl = sum(t.pnl for t in trades if t.pnl)
        
        # ROI 계산 (총 투자금 대비)
        total_investment = sum(abs(t.entry_price * t.size) for t in trades if t.entry_price and t.size)
        roi = (total_pnl / total_investment * 100) if total_investment > 0 else 0

        # 평균 승/패
        wins = [t.pnl for t in trades if t.pnl and t.pnl > 0]
        losses = [t.pnl for t in trades if t.pnl and t.pnl <= 0]
        avg_win = sum(wins) / len(wins) if wins else 0
        avg_loss = sum(losses) / len(losses) if losses else 0

        # Profit Factor
        total_wins = sum(wins) if wins else 0
        total_losses = abs(sum(losses)) if losses else 0
        profit_factor = (total_wins / total_losses) if total_losses > 0 else 0

        return {
            "user_id": user_id,
            "win_rate": win_rate,
            "total_trades": total_trades,
            "winning_trades": winning_trades,
            "losing_trades": losing_trades,
            "total_pnl": total_pnl,
            "roi": roi,
            "avg_win": avg_win,
            "avg_loss": avg_loss,
            "profit_factor": profit_factor,
            "last_trade_at": max((t.created_at for t in trades), default=None)
        }

    async def update_leaderboard(self, period: str = "monthly") -> int:
        """
        리더보드 업데이트 (크론잡으로 주기적 실행)

        Args:
            period: 업데이트할 기간

        Returns:
            업데이트된 항목 수
        """
        logger.info(f"Starting leaderboard update for period: {period}")

        period_start, period_end = self.calculate_period_dates(period)

        # 해당 기간에 거래한 모든 사용자 조회
        active_user_ids = self.db.query(Trade.user_id).filter(
            and_(
                Trade.created_at >= period_start,
                Trade.created_at < period_end
            )
        ).distinct().all()

        updated_count = 0

        for (user_id,) in active_user_ids:
            performance = await self.calculate_user_performance(
                user_id, period_start, period_end
            )

            if not performance:
                continue

            # 기존 항목 조회 또는 생성
            entry = self.db.query(LeaderboardEntry).filter(
                and_(
                    LeaderboardEntry.user_id == user_id,
                    LeaderboardEntry.period == period
                )
            ).first()

            if entry:
                # 기존 순위 저장
                entry.previous_rank = entry.rank
                # 성과 업데이트
                for key, value in performance.items():
                    if key != "user_id":
                        setattr(entry, key, value)
            else:
                # 새 항목 생성
                entry = LeaderboardEntry(
                    period=period,
                    period_start=period_start,
                    period_end=period_end,
                    **performance
                )
                self.db.add(entry)

            updated_count += 1

        self.db.commit()

        # 순위 재계산
        await self.recalculate_rankings(period)

        logger.info(f"Leaderboard update completed: {updated_count} entries updated")
        return updated_count

    async def recalculate_rankings(self, period: str):
        """
        ROI 기준으로 순위 재계산
        """
        entries = self.db.query(LeaderboardEntry).filter(
            LeaderboardEntry.period == period
        ).order_by(LeaderboardEntry.roi.desc()).all()

        for rank, entry in enumerate(entries, start=1):
            entry.rank = rank
            entry.calculate_rank_change()

        self.db.commit()
        logger.info(f"Rankings recalculated for {len(entries)} entries in period: {period}")

    async def get_leaderboard(
        self,
        period: str = "monthly",
        limit: int = 100,
        offset: int = 0,
        public_only: bool = True
    ) -> List[LeaderboardEntry]:
        """
        리더보드 조회

        Args:
            period: 조회 기간
            limit: 반환할 최대 항목 수
            offset: 페이징 오프셋
            public_only: 공개 프로필만 조회

        Returns:
            LeaderboardEntry 리스트
        """
        query = self.db.query(LeaderboardEntry).filter(
            LeaderboardEntry.period == period
        )

        if public_only:
            query = query.filter(LeaderboardEntry.is_public == True)

        return query.order_by(
            LeaderboardEntry.rank.asc()
        ).limit(limit).offset(offset).all()

    async def get_user_rank(self, user_id: str, period: str = "monthly") -> Optional[LeaderboardEntry]:
        """특정 사용자의 랭킹 조회"""
        return self.db.query(LeaderboardEntry).filter(
            and_(
                LeaderboardEntry.user_id == user_id,
                LeaderboardEntry.period == period
            )
        ).first()
