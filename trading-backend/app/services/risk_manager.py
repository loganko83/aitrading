"""
Risk Management System

Implements comprehensive risk management:
- Position sizing based on risk tolerance
- ATR-based dynamic stop-loss/take-profit
- Maximum drawdown protection
- Leverage management
- Portfolio risk monitoring
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional, Tuple
from dataclasses import dataclass
import logging

from app.services.margin_calculator import MarginCalculator
from app.strategies.indicators import calculate_atr

logger = logging.getLogger(__name__)


@dataclass
class RiskParameters:
    """Risk management parameters"""
    max_position_size_pct: float = 0.10  # 10% of capital per trade
    max_risk_per_trade_pct: float = 0.02  # 2% max loss per trade
    max_daily_loss_pct: float = 0.05  # 5% max daily loss
    max_drawdown_pct: float = 0.20  # 20% max drawdown before stopping
    atr_multiplier_sl: float = 1.5  # ATR multiplier for stop-loss
    atr_multiplier_tp: float = 3.0  # ATR multiplier for take-profit
    risk_reward_ratio: float = 2.0  # Minimum risk/reward ratio
    max_open_positions: int = 3  # Maximum simultaneous positions
    max_leverage: int = 10  # Maximum allowed leverage


@dataclass
class PositionRisk:
    """Risk analysis for a position"""
    symbol: str
    position_size: float
    position_value: float
    leverage: int
    entry_price: float
    stop_loss: float
    take_profit: float
    risk_amount: float
    reward_amount: float
    risk_reward_ratio: float
    risk_pct: float
    margin_required: float
    liquidation_price: float


class RiskManager:
    """
    Risk Management System

    Manages all risk-related calculations and validates trades against risk limits.
    """

    def __init__(
        self,
        initial_capital: float,
        params: Optional[RiskParameters] = None
    ):
        """
        Initialize risk manager

        Args:
            initial_capital: Initial trading capital
            params: Risk parameters (defaults to RiskParameters())
        """
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.params = params or RiskParameters()

        # Tracking
        self.daily_pnl = 0.0
        self.peak_capital = initial_capital
        self.current_drawdown = 0.0
        self.open_positions = 0

    def calculate_position_size(
        self,
        symbol: str,
        entry_price: float,
        stop_loss: float,
        leverage: int,
        df: pd.DataFrame
    ) -> float:
        """
        Calculate optimal position size based on risk parameters

        Uses Kelly Criterion-inspired sizing with risk limits.

        Args:
            symbol: Trading symbol
            entry_price: Planned entry price
            stop_loss: Stop-loss price
            leverage: Desired leverage
            df: Historical data for volatility calculation

        Returns:
            Position size in base currency
        """
        # Calculate ATR for volatility assessment
        atr = calculate_atr(df, period=14)
        current_atr = atr.iloc[-1]

        # Risk per unit
        risk_per_unit = abs(entry_price - stop_loss)

        # Maximum risk amount (2% of capital)
        max_risk_amount = self.current_capital * self.params.max_risk_per_trade_pct

        # Position size based on risk
        position_size_risk = max_risk_amount / risk_per_unit

        # Maximum position value (10% of capital × leverage)
        max_position_value = self.current_capital * self.params.max_position_size_pct * leverage
        position_size_capital = max_position_value / entry_price

        # Use the smaller of the two
        position_size = min(position_size_risk, position_size_capital)

        # Verify margin requirements
        initial_margin = MarginCalculator.calculate_initial_margin(
            position_size, entry_price, leverage
        )

        # Check if we have sufficient capital
        if initial_margin > self.current_capital * self.params.max_position_size_pct:
            # Reduce position size to fit capital
            position_size = (self.current_capital * self.params.max_position_size_pct * leverage) / entry_price

        logger.info(f"Calculated position size: {position_size:.4f} {symbol} "
                   f"(${position_size * entry_price:,.2f})")

        return position_size

    def calculate_stop_loss_take_profit(
        self,
        entry_price: float,
        direction: str,
        df: pd.DataFrame,
        atr_multiplier_sl: Optional[float] = None,
        atr_multiplier_tp: Optional[float] = None
    ) -> Tuple[float, float]:
        """
        Calculate dynamic stop-loss and take-profit using ATR

        Args:
            entry_price: Entry price
            direction: 'LONG' or 'SHORT'
            df: Historical data for ATR calculation
            atr_multiplier_sl: ATR multiplier for SL (default from params)
            atr_multiplier_tp: ATR multiplier for TP (default from params)

        Returns:
            Tuple of (stop_loss, take_profit)
        """
        # Use defaults if not provided
        atr_sl = atr_multiplier_sl or self.params.atr_multiplier_sl
        atr_tp = atr_multiplier_tp or self.params.atr_multiplier_tp

        # Calculate ATR
        atr = calculate_atr(df, period=14)
        current_atr = atr.iloc[-1]

        if direction == 'LONG':
            stop_loss = entry_price - (current_atr * atr_sl)
            take_profit = entry_price + (current_atr * atr_tp)
        else:  # SHORT
            stop_loss = entry_price + (current_atr * atr_sl)
            take_profit = entry_price - (current_atr * atr_tp)

        return stop_loss, take_profit

    def validate_trade(
        self,
        symbol: str,
        position_size: float,
        entry_price: float,
        stop_loss: float,
        take_profit: float,
        leverage: int,
        direction: str
    ) -> Tuple[bool, str, Optional[PositionRisk]]:
        """
        Validate if trade meets risk requirements

        Args:
            symbol: Trading symbol
            position_size: Position size
            entry_price: Entry price
            stop_loss: Stop-loss price
            take_profit: Take-profit price
            leverage: Leverage
            direction: 'LONG' or 'SHORT'

        Returns:
            Tuple of (is_valid, reason, position_risk)
        """
        # Check maximum open positions
        if self.open_positions >= self.params.max_open_positions:
            return False, f"Maximum open positions reached ({self.params.max_open_positions})", None

        # Check leverage limit
        if leverage > self.params.max_leverage:
            return False, f"Leverage {leverage}x exceeds maximum {self.params.max_leverage}x", None

        # Check daily loss limit
        daily_loss_pct = (self.daily_pnl / self.initial_capital) * 100
        if daily_loss_pct <= -self.params.max_daily_loss_pct * 100:
            return False, f"Daily loss limit reached ({daily_loss_pct:.2f}%)", None

        # Check maximum drawdown
        self.current_drawdown = ((self.peak_capital - self.current_capital) / self.peak_capital) * 100
        if self.current_drawdown >= self.params.max_drawdown_pct * 100:
            return False, f"Maximum drawdown reached ({self.current_drawdown:.2f}%)", None

        # Calculate position risk
        position_value = position_size * entry_price

        # Risk and reward amounts
        risk_per_unit = abs(entry_price - stop_loss)
        reward_per_unit = abs(take_profit - entry_price)

        risk_amount = position_size * risk_per_unit
        reward_amount = position_size * reward_per_unit

        # Risk/reward ratio
        risk_reward_ratio = reward_amount / risk_amount if risk_amount > 0 else 0

        # Check minimum risk/reward ratio
        if risk_reward_ratio < self.params.risk_reward_ratio:
            return False, f"Risk/reward ratio {risk_reward_ratio:.2f} below minimum {self.params.risk_reward_ratio}", None

        # Check risk percentage
        risk_pct = (risk_amount / self.current_capital) * 100
        if risk_pct > self.params.max_risk_per_trade_pct * 100:
            return False, f"Risk {risk_pct:.2f}% exceeds maximum {self.params.max_risk_per_trade_pct * 100}%", None

        # Calculate margin requirements
        initial_margin = MarginCalculator.calculate_initial_margin(
            position_size, entry_price, leverage
        )

        # Check margin availability
        if initial_margin > self.current_capital * self.params.max_position_size_pct:
            return False, f"Insufficient margin (required: ${initial_margin:.2f})", None

        # Calculate liquidation price
        liquidation_price = MarginCalculator.calculate_liquidation_price(
            entry_price, position_size, direction, leverage, self.current_capital
        )

        # Create position risk object
        position_risk = PositionRisk(
            symbol=symbol,
            position_size=position_size,
            position_value=position_value,
            leverage=leverage,
            entry_price=entry_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            risk_amount=risk_amount,
            reward_amount=reward_amount,
            risk_reward_ratio=risk_reward_ratio,
            risk_pct=risk_pct,
            margin_required=initial_margin,
            liquidation_price=liquidation_price
        )

        return True, "Trade validated successfully", position_risk

    def update_capital(self, pnl: float):
        """
        Update capital after trade close

        Args:
            pnl: Profit/loss amount
        """
        self.current_capital += pnl
        self.daily_pnl += pnl

        # Update peak capital
        if self.current_capital > self.peak_capital:
            self.peak_capital = self.current_capital

        logger.info(f"Capital updated: ${self.current_capital:,.2f} (P&L: ${pnl:+,.2f})")

    def reset_daily_tracking(self):
        """Reset daily P&L tracking (call at start of each trading day)"""
        self.daily_pnl = 0.0
        logger.info("Daily tracking reset")

    def get_risk_status(self) -> Dict:
        """
        Get current risk status

        Returns:
            Dictionary with risk metrics
        """
        return {
            'current_capital': self.current_capital,
            'peak_capital': self.peak_capital,
            'current_drawdown_pct': self.current_drawdown,
            'daily_pnl': self.daily_pnl,
            'daily_pnl_pct': (self.daily_pnl / self.initial_capital) * 100,
            'open_positions': self.open_positions,
            'max_open_positions': self.params.max_open_positions,
            'risk_limits': {
                'max_position_size_pct': self.params.max_position_size_pct * 100,
                'max_risk_per_trade_pct': self.params.max_risk_per_trade_pct * 100,
                'max_daily_loss_pct': self.params.max_daily_loss_pct * 100,
                'max_drawdown_pct': self.params.max_drawdown_pct * 100
            },
            'can_trade': (
                self.open_positions < self.params.max_open_positions and
                (self.daily_pnl / self.initial_capital) > -self.params.max_daily_loss_pct and
                self.current_drawdown < self.params.max_drawdown_pct * 100
            )
        }
