"""
Copy Trading Models

카피 트레이딩 시스템
- 리더-팔로워 관계
- 자동 주문 복제
- 수익 공유 추적
"""

from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, ForeignKey, Index, Text
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.database.base import Base


class CopyRelationship(Base):
    """
    카피 트레이딩 관계 모델

    팔로워가 리더의 거래를 자동으로 복제
    """
    __tablename__ = "copy_relationships"

    # Primary Keys
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    follower_id = Column(String, ForeignKey("users.id"), nullable=False)  # 카피하는 사람
    leader_id = Column(String, ForeignKey("users.id"), nullable=False)    # 카피당하는 사람
    strategy_id = Column(String, ForeignKey("strategies.id"), nullable=True)

    # Copy Settings
    copy_ratio = Column(Float, default=1.0, nullable=False)  # 0.1 ~ 2.0 (10% ~ 200%)
    max_position_size = Column(Float, nullable=True)  # Maximum position size in USDT
    min_position_size = Column(Float, default=10.0)  # Minimum position size in USDT

    # Risk Management
    stop_loss_multiplier = Column(Float, default=1.0)  # SL multiplier (1.0 = same as leader)
    take_profit_multiplier = Column(Float, default=1.0)  # TP multiplier
    max_daily_loss = Column(Float, nullable=True)  # Max daily loss in USDT
    max_daily_trades = Column(Integer, default=100)  # Max trades per day

    # Status
    is_active = Column(Boolean, default=True)
    auto_start = Column(Boolean, default=True)  # Auto-start copying new positions
    copy_close_only = Column(Boolean, default=False)  # Only copy close orders (not entry)

    # Profit Sharing
    profit_share_percentage = Column(Float, default=10.0)  # Follower shares 10% profit with leader
    total_shared_profit = Column(Float, default=0.0)  # Total profit shared (USDT)
    pending_payout = Column(Float, default=0.0)  # Pending payout to leader

    # Statistics
    total_copied_trades = Column(Integer, default=0)
    successful_copies = Column(Integer, default=0)
    failed_copies = Column(Integer, default=0)
    total_pnl = Column(Float, default=0.0)  # Follower's total PnL from copying

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_copied_at = Column(DateTime, nullable=True)
    paused_at = Column(DateTime, nullable=True)  # When temporarily paused

    # Relationships
    follower = relationship("User", foreign_keys=[follower_id], backref="following")
    leader = relationship("User", foreign_keys=[leader_id], backref="followers")

    # Indexes
    __table_args__ = (
        Index('idx_copy_follower_active', 'follower_id', 'is_active'),
        Index('idx_copy_leader_active', 'leader_id', 'is_active'),
        Index('idx_copy_relationship', 'follower_id', 'leader_id'),
    )

    def __repr__(self):
        return f"<CopyRelationship(follower={self.follower_id}, leader={self.leader_id}, ratio={self.copy_ratio})>"

    def calculate_position_size(self, leader_position_size: float, leader_price: float) -> float:
        """
        Calculate follower's position size based on copy ratio

        Args:
            leader_position_size: Leader's position size in contracts/coins
            leader_price: Current price

        Returns:
            Follower's position size in contracts/coins
        """
        # Calculate base copy size
        copy_size = leader_position_size * self.copy_ratio

        # Apply max position size limit
        if self.max_position_size:
            max_size_in_contracts = self.max_position_size / leader_price
            copy_size = min(copy_size, max_size_in_contracts)

        # Apply min position size limit
        min_size_in_contracts = self.min_position_size / leader_price
        if copy_size < min_size_in_contracts:
            return 0  # Position too small, skip

        return copy_size

    def can_copy_trade(self) -> tuple[bool, str]:
        """
        Check if follower can copy leader's trade

        Returns:
            (can_copy: bool, reason: str)
        """
        if not self.is_active:
            return False, "Copy relationship is inactive"

        if self.paused_at:
            return False, "Copy relationship is paused"

        # Check daily trade limit
        if self.max_daily_trades and self.total_copied_trades >= self.max_daily_trades:
            return False, "Daily trade limit reached"

        # Check daily loss limit
        if self.max_daily_loss and abs(self.total_pnl) >= self.max_daily_loss:
            return False, "Daily loss limit reached"

        return True, "OK"

    def record_copy_attempt(self, success: bool, pnl: float = 0):
        """Record a copy trade attempt"""
        self.total_copied_trades += 1
        if success:
            self.successful_copies += 1
            self.total_pnl += pnl
        else:
            self.failed_copies += 1

        self.last_copied_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def to_dict(self):
        """API response dict"""
        return {
            "id": self.id,
            "follower_id": self.follower_id,
            "leader_id": self.leader_id,
            "strategy_id": self.strategy_id,
            "copy_ratio": self.copy_ratio,
            "max_position_size": self.max_position_size,
            "is_active": self.is_active,
            "total_copied_trades": self.total_copied_trades,
            "successful_copies": self.successful_copies,
            "failed_copies": self.failed_copies,
            "total_pnl": round(self.total_pnl, 2),
            "profit_share_percentage": self.profit_share_percentage,
            "total_shared_profit": round(self.total_shared_profit, 2),
            "created_at": self.created_at.isoformat(),
            "last_copied_at": self.last_copied_at.isoformat() if self.last_copied_at else None
        }


class CopiedTrade(Base):
    """
    복제된 거래 기록

    각 카피 거래의 상세 내역을 추적
    """
    __tablename__ = "copied_trades"

    # Primary Keys
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    copy_relationship_id = Column(String, ForeignKey("copy_relationships.id"), nullable=False)

    # Trade References
    leader_trade_id = Column(String, ForeignKey("trades.id"), nullable=True)
    follower_trade_id = Column(String, ForeignKey("trades.id"), nullable=True)
    leader_order_id = Column(String, nullable=True)  # Leader's exchange order ID
    follower_order_id = Column(String, nullable=True)  # Follower's exchange order ID

    # Trade Details
    symbol = Column(String, nullable=False)
    side = Column(String, nullable=False)  # "buy", "sell", "close_long", "close_short"
    order_type = Column(String, default="market")  # "market", "limit"

    # Quantities and Prices
    leader_quantity = Column(Float, nullable=False)
    follower_quantity = Column(Float, nullable=False)
    leader_entry_price = Column(Float, nullable=True)
    follower_entry_price = Column(Float, nullable=True)

    # Copy Settings Used
    copy_ratio_used = Column(Float, nullable=False)

    # Execution Status
    status = Column(String, default="pending")
    # Status: "pending", "executed", "failed", "cancelled", "partial"

    execution_time_ms = Column(Integer, nullable=True)  # Execution delay in milliseconds
    slippage = Column(Float, nullable=True)  # Price slippage %

    # PnL Tracking
    follower_pnl = Column(Float, default=0.0)
    profit_shared = Column(Float, default=0.0)  # Profit shared with leader

    # Error Tracking
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)

    # Timestamps
    leader_order_time = Column(DateTime, nullable=True)
    follower_order_time = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    copy_relationship = relationship("CopyRelationship", backref="copied_trades")

    # Indexes
    __table_args__ = (
        Index('idx_copied_relationship_time', 'copy_relationship_id', 'created_at'),
        Index('idx_copied_status', 'status'),
        Index('idx_copied_leader_trade', 'leader_trade_id'),
        Index('idx_copied_follower_trade', 'follower_trade_id'),
    )

    def __repr__(self):
        return f"<CopiedTrade(id={self.id}, symbol={self.symbol}, status={self.status})>"

    def calculate_slippage(self):
        """Calculate price slippage between leader and follower"""
        if self.leader_entry_price and self.follower_entry_price:
            slippage = (
                (self.follower_entry_price - self.leader_entry_price)
                / self.leader_entry_price
                * 100
            )
            self.slippage = round(slippage, 4)

    def to_dict(self):
        """API response dict"""
        return {
            "id": self.id,
            "copy_relationship_id": self.copy_relationship_id,
            "symbol": self.symbol,
            "side": self.side,
            "leader_quantity": self.leader_quantity,
            "follower_quantity": self.follower_quantity,
            "leader_entry_price": self.leader_entry_price,
            "follower_entry_price": self.follower_entry_price,
            "status": self.status,
            "follower_pnl": round(self.follower_pnl, 2) if self.follower_pnl else 0,
            "profit_shared": round(self.profit_shared, 2) if self.profit_shared else 0,
            "slippage": self.slippage,
            "execution_time_ms": self.execution_time_ms,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat()
        }
