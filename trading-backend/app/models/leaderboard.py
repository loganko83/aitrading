"""
Leaderboard Models

실시간 트레이더 랭킹 시스템
- 일일/주간/월간/전체 기간별 리더보드
- 승률, ROI, Sharpe Ratio 등 다양한 성과 지표
- 카피 트레이딩 연동
"""

from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.database.base import Base


class LeaderboardEntry(Base):
    """
    리더보드 항목 모델

    각 트레이더의 성과를 기간별로 추적
    실시간 랭킹 계산을 위해 Redis와 연동
    """
    __tablename__ = "leaderboard"

    # Primary Keys
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    strategy_id = Column(String, ForeignKey("strategies.id"), nullable=True)

    # Performance Metrics
    win_rate = Column(Float, default=0.0)  # 승률 (0-100)
    total_trades = Column(Integer, default=0)  # 총 거래 횟수
    winning_trades = Column(Integer, default=0)  # 승리한 거래
    losing_trades = Column(Integer, default=0)  # 손실 거래

    total_pnl = Column(Float, default=0.0)  # 총 손익 (USDT)
    total_pnl_percentage = Column(Float, default=0.0)  # 총 손익률 (%)
    roi = Column(Float, default=0.0)  # ROI (%)

    sharpe_ratio = Column(Float, default=0.0)  # Sharpe Ratio
    max_drawdown = Column(Float, default=0.0)  # 최대 낙폭 (%)
    profit_factor = Column(Float, default=0.0)  # Profit Factor

    avg_win = Column(Float, default=0.0)  # 평균 이익 (USDT)
    avg_loss = Column(Float, default=0.0)  # 평균 손실 (USDT)

    # Ranking
    rank = Column(Integer, nullable=True)  # 순위
    previous_rank = Column(Integer, nullable=True)  # 이전 순위 (변동 추적)
    rank_change = Column(Integer, default=0)  # 순위 변동 (양수: 상승, 음수: 하락)

    # Time Period
    period = Column(String, nullable=False, default="monthly")
    # Options: "daily", "weekly", "monthly", "all_time"
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)

    # Social Features
    is_public = Column(Boolean, default=False)  # 공개 여부
    allow_copy = Column(Boolean, default=False)  # 카피 트레이딩 허용
    copy_count = Column(Integer, default=0)  # 카피한 사용자 수

    # Metadata
    last_trade_at = Column(DateTime, nullable=True)  # 마지막 거래 시각
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="leaderboard_entries")

    # Indexes for performance
    __table_args__ = (
        Index('idx_leaderboard_period_rank', 'period', 'rank'),
        Index('idx_leaderboard_user_period', 'user_id', 'period'),
        Index('idx_leaderboard_roi', 'roi'),
        Index('idx_leaderboard_win_rate', 'win_rate'),
        Index('idx_leaderboard_public', 'is_public', 'period'),
    )

    def __repr__(self):
        return f"<LeaderboardEntry(user_id={self.user_id}, rank={self.rank}, roi={self.roi}%, period={self.period})>"

    def calculate_rank_change(self):
        """순위 변동 계산"""
        if self.previous_rank and self.rank:
            self.rank_change = self.previous_rank - self.rank
        else:
            self.rank_change = 0

    def to_dict(self):
        """API 응답용 딕셔너리 변환"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "strategy_id": self.strategy_id,
            "rank": self.rank,
            "rank_change": self.rank_change,
            "win_rate": round(self.win_rate, 2),
            "total_trades": self.total_trades,
            "total_pnl": round(self.total_pnl, 2),
            "roi": round(self.roi, 2),
            "sharpe_ratio": round(self.sharpe_ratio, 2),
            "max_drawdown": round(self.max_drawdown, 2),
            "profit_factor": round(self.profit_factor, 2),
            "copy_count": self.copy_count,
            "allow_copy": self.allow_copy,
            "period": self.period,
            "last_trade_at": self.last_trade_at.isoformat() if self.last_trade_at else None,
            "updated_at": self.updated_at.isoformat()
        }


class LeaderboardBadge(Base):
    """
    리더보드 배지/업적 시스템

    Top 트레이더에게 부여되는 배지
    예: "Top 10", "Best Win Rate", "Most Consistent"
    """
    __tablename__ = "leaderboard_badges"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)

    # Badge Info
    badge_type = Column(String, nullable=False)
    # Types: "top_10", "top_1", "best_win_rate", "most_consistent",
    #        "highest_roi", "trader_of_month", "legend"

    badge_name = Column(String, nullable=False)  # "Top 10 Trader"
    badge_description = Column(String, nullable=True)
    badge_icon = Column(String, nullable=True)  # Icon URL or emoji

    # Achievement Details
    period = Column(String, nullable=False)  # "monthly", "weekly", etc.
    achieved_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)  # 일부 배지는 만료됨

    # Metadata
    badge_metadata = Column(String, nullable=True)  # JSON string for additional data

    is_active = Column(Boolean, default=True)

    # Relationships
    user = relationship("User", back_populates="badges")

    def __repr__(self):
        return f"<LeaderboardBadge(user_id={self.user_id}, type={self.badge_type}, name={self.badge_name})>"

    def to_dict(self):
        return {
            "id": self.id,
            "badge_type": self.badge_type,
            "badge_name": self.badge_name,
            "badge_description": self.badge_description,
            "badge_icon": self.badge_icon,
            "period": self.period,
            "achieved_at": self.achieved_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "is_active": self.is_active
        }
