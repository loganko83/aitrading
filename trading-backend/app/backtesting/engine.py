"""
Backtest Engine

Simulates trading strategies on historical OHLCV data.
Supports:
- Any strategy from strategies module
- Transaction costs (fees)
- Leverage simulation
- Position sizing
- Performance metrics calculation
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import logging

from app.strategies.strategies import BaseStrategy, Signal
from .metrics import PerformanceMetrics

logger = logging.getLogger(__name__)


@dataclass
class Trade:
    """Represents a single trade"""
    entry_time: datetime
    entry_price: float
    direction: str  # 'LONG' or 'SHORT'
    quantity: float
    leverage: int
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    exit_time: Optional[datetime] = None
    exit_price: Optional[float] = None
    exit_reason: str = ""  # 'stop_loss', 'take_profit', 'signal', 'end'
    pnl: float = 0.0
    pnl_pct: float = 0.0
    fees: float = 0.0


@dataclass
class BacktestResult:
    """Complete backtest results"""
    # Strategy info
    strategy_name: str
    start_date: datetime
    end_date: datetime

    # Performance metrics
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    win_rate: float = 0.0

    # Returns
    total_return: float = 0.0
    total_return_pct: float = 0.0
    avg_return_per_trade: float = 0.0

    # Risk metrics
    max_drawdown: float = 0.0
    max_drawdown_pct: float = 0.0
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0

    # Trade details
    trades: List[Trade] = field(default_factory=list)
    equity_curve: pd.Series = field(default_factory=pd.Series)
    drawdown_curve: pd.Series = field(default_factory=pd.Series)

    # Detailed stats
    avg_win: float = 0.0
    avg_loss: float = 0.0
    profit_factor: float = 0.0
    max_consecutive_wins: int = 0
    max_consecutive_losses: int = 0


class BacktestEngine:
    """
    Backtesting Engine for Trading Strategies

    Simulates strategy execution on historical data with realistic conditions:
    - Transaction costs (maker/taker fees)
    - Leverage support
    - Stop-loss and take-profit execution
    - Position sizing
    """

    def __init__(
        self,
        initial_capital: float = 10000.0,
        maker_fee: float = 0.0002,  # 0.02% Binance Futures maker
        taker_fee: float = 0.0004,  # 0.04% Binance Futures taker
        leverage: int = 3,
        position_size_pct: float = 0.10,  # 10% of capital per trade
        risk_free_rate: float = 0.02  # 2% annual for Sharpe ratio
    ):
        """
        Initialize backtest engine

        Args:
            initial_capital: Starting capital in USDT
            maker_fee: Maker fee percentage (default 0.0002 = 0.02%)
            taker_fee: Taker fee percentage (default 0.0004 = 0.04%)
            leverage: Trading leverage (default 3x)
            position_size_pct: % of capital to use per trade (default 10%)
            risk_free_rate: Annual risk-free rate for Sharpe ratio (default 2%)
        """
        self.initial_capital = initial_capital
        self.maker_fee = maker_fee
        self.taker_fee = taker_fee
        self.leverage = leverage
        self.position_size_pct = position_size_pct
        self.risk_free_rate = risk_free_rate

        # State variables
        self.capital = initial_capital
        self.equity = initial_capital
        self.position: Optional[Trade] = None

    def run(
        self,
        strategy: BaseStrategy,
        df: pd.DataFrame,
        symbol: str = "BTCUSDT"
    ) -> BacktestResult:
        """
        Run backtest simulation

        Args:
            strategy: Trading strategy instance
            df: Historical OHLCV DataFrame with columns: timestamp, open, high, low, close, volume
            symbol: Trading symbol (for logging)

        Returns:
            BacktestResult with complete performance analysis
        """
        logger.info(f"Starting backtest for {strategy.name} on {symbol}")
        logger.info(f"Period: {df['timestamp'].iloc[0]} to {df['timestamp'].iloc[-1]}")
        logger.info(f"Initial capital: ${self.initial_capital:,.2f}")

        # Reset state
        self.capital = self.initial_capital
        self.equity = self.initial_capital
        self.position = None

        # Track performance
        trades: List[Trade] = []
        equity_history = []
        timestamps = []

        # Iterate through historical data
        for i in range(len(df)):
            row = df.iloc[i]
            current_price = row['close']
            current_time = row['timestamp']

            # Check if we need to exit current position (stop-loss/take-profit)
            if self.position:
                exit_signal = self._check_exit_conditions(row)

                if exit_signal:
                    # Close position
                    closed_trade = self._close_position(
                        exit_price=exit_signal['price'],
                        exit_time=current_time,
                        exit_reason=exit_signal['reason']
                    )
                    trades.append(closed_trade)

            # Generate new signal if no position
            if not self.position:
                signal = strategy.generate_signal(df.iloc[:i+1].copy(), current_price)

                if signal.should_enter:
                    # Open new position
                    self._open_position(
                        signal=signal,
                        entry_time=current_time
                    )

            # Update equity
            if self.position:
                # Calculate unrealized P&L
                unrealized_pnl = self._calculate_pnl(
                    self.position.entry_price,
                    current_price,
                    self.position.direction,
                    self.position.quantity,
                    self.position.leverage
                )
                self.equity = self.capital + unrealized_pnl
            else:
                self.equity = self.capital

            equity_history.append(self.equity)
            timestamps.append(current_time)

        # Close any remaining position at the end
        if self.position:
            final_price = df.iloc[-1]['close']
            final_time = df.iloc[-1]['timestamp']
            closed_trade = self._close_position(
                exit_price=final_price,
                exit_time=final_time,
                exit_reason='end'
            )
            trades.append(closed_trade)

        # Calculate performance metrics
        result = self._calculate_results(
            strategy_name=strategy.name,
            trades=trades,
            equity_history=equity_history,
            timestamps=timestamps,
            start_date=df['timestamp'].iloc[0],
            end_date=df['timestamp'].iloc[-1]
        )

        logger.info(f"Backtest completed: {result.total_trades} trades, "
                   f"{result.win_rate:.1f}% win rate, "
                   f"{result.total_return_pct:+.2f}% return")

        return result

    def _open_position(self, signal: Signal, entry_time: datetime):
        """Open new position based on signal"""

        # Calculate position size
        position_value = self.capital * self.position_size_pct * self.leverage
        quantity = position_value / signal.entry_price

        # Calculate entry fee (taker fee for market orders)
        entry_fee = position_value * self.taker_fee

        # Create trade
        self.position = Trade(
            entry_time=entry_time,
            entry_price=signal.entry_price,
            direction=signal.direction,
            quantity=quantity,
            leverage=self.leverage,
            stop_loss=signal.stop_loss,
            take_profit=signal.take_profit,
            fees=entry_fee
        )

        # Deduct entry fee from capital
        self.capital -= entry_fee

        logger.debug(f"Opened {signal.direction} position at ${signal.entry_price:.2f}, "
                    f"qty={quantity:.4f}, SL=${signal.stop_loss:.2f}, TP=${signal.take_profit:.2f}")

    def _close_position(
        self,
        exit_price: float,
        exit_time: datetime,
        exit_reason: str
    ) -> Trade:
        """Close current position and calculate P&L"""

        if not self.position:
            raise ValueError("No position to close")

        # Calculate P&L
        pnl = self._calculate_pnl(
            self.position.entry_price,
            exit_price,
            self.position.direction,
            self.position.quantity,
            self.position.leverage
        )

        # Calculate exit fee
        position_value = self.position.quantity * exit_price
        exit_fee = position_value * self.taker_fee

        # Total P&L after fees
        net_pnl = pnl - exit_fee

        # Update position
        self.position.exit_time = exit_time
        self.position.exit_price = exit_price
        self.position.exit_reason = exit_reason
        self.position.pnl = net_pnl
        self.position.pnl_pct = (net_pnl / (self.capital + net_pnl)) * 100
        self.position.fees += exit_fee

        # Update capital
        self.capital += net_pnl

        logger.debug(f"Closed {self.position.direction} position at ${exit_price:.2f}, "
                    f"P&L=${net_pnl:+.2f} ({self.position.pnl_pct:+.2f}%), "
                    f"Reason: {exit_reason}")

        # Save and clear position
        closed_trade = self.position
        self.position = None

        return closed_trade

    def _check_exit_conditions(self, row: pd.Series) -> Optional[Dict]:
        """Check if stop-loss or take-profit is hit"""

        if not self.position:
            return None

        high = row['high']
        low = row['low']

        # Check stop-loss
        if self.position.stop_loss:
            if self.position.direction == 'LONG' and low <= self.position.stop_loss:
                return {'price': self.position.stop_loss, 'reason': 'stop_loss'}
            elif self.position.direction == 'SHORT' and high >= self.position.stop_loss:
                return {'price': self.position.stop_loss, 'reason': 'stop_loss'}

        # Check take-profit
        if self.position.take_profit:
            if self.position.direction == 'LONG' and high >= self.position.take_profit:
                return {'price': self.position.take_profit, 'reason': 'take_profit'}
            elif self.position.direction == 'SHORT' and low <= self.position.take_profit:
                return {'price': self.position.take_profit, 'reason': 'take_profit'}

        return None

    def _calculate_pnl(
        self,
        entry_price: float,
        exit_price: float,
        direction: str,
        quantity: float,
        leverage: int
    ) -> float:
        """Calculate P&L for a position"""

        if direction == 'LONG':
            pnl = (exit_price - entry_price) * quantity
        else:  # SHORT
            pnl = (entry_price - exit_price) * quantity

        return pnl

    def _calculate_results(
        self,
        strategy_name: str,
        trades: List[Trade],
        equity_history: List[float],
        timestamps: List[datetime],
        start_date: datetime,
        end_date: datetime
    ) -> BacktestResult:
        """Calculate comprehensive backtest results"""

        result = BacktestResult(
            strategy_name=strategy_name,
            start_date=start_date,
            end_date=end_date,
            trades=trades
        )

        # Basic trade statistics
        result.total_trades = len(trades)

        if result.total_trades == 0:
            logger.warning("No trades executed during backtest period")
            return result

        # Win/loss statistics
        winning_trades = [t for t in trades if t.pnl > 0]
        losing_trades = [t for t in trades if t.pnl < 0]

        result.winning_trades = len(winning_trades)
        result.losing_trades = len(losing_trades)
        result.win_rate = (result.winning_trades / result.total_trades) * 100

        # Returns
        result.total_return = self.capital - self.initial_capital
        result.total_return_pct = (result.total_return / self.initial_capital) * 100
        result.avg_return_per_trade = result.total_return / result.total_trades

        # Win/loss averages
        if winning_trades:
            result.avg_win = np.mean([t.pnl for t in winning_trades])
        if losing_trades:
            result.avg_loss = abs(np.mean([t.pnl for t in losing_trades]))

        # Profit factor
        total_wins = sum(t.pnl for t in winning_trades) if winning_trades else 0
        total_losses = abs(sum(t.pnl for t in losing_trades)) if losing_trades else 0
        result.profit_factor = total_wins / total_losses if total_losses > 0 else float('inf')

        # Equity curve and drawdown
        equity_series = pd.Series(equity_history, index=timestamps)
        result.equity_curve = equity_series

        # Calculate drawdown
        running_max = equity_series.cummax()
        drawdown = equity_series - running_max
        result.drawdown_curve = drawdown

        result.max_drawdown = abs(drawdown.min())
        result.max_drawdown_pct = (result.max_drawdown / running_max[drawdown.idxmin()]) * 100

        # Sharpe ratio
        returns = equity_series.pct_change().dropna()
        if len(returns) > 0:
            excess_returns = returns - (self.risk_free_rate / 252)  # Daily risk-free rate
            result.sharpe_ratio = np.sqrt(252) * (excess_returns.mean() / excess_returns.std()) if excess_returns.std() > 0 else 0

            # Sortino ratio (downside deviation)
            downside_returns = returns[returns < 0]
            if len(downside_returns) > 0:
                downside_std = downside_returns.std()
                result.sortino_ratio = np.sqrt(252) * (excess_returns.mean() / downside_std) if downside_std > 0 else 0

        # Consecutive wins/losses
        consecutive_wins = 0
        consecutive_losses = 0
        max_consecutive_wins = 0
        max_consecutive_losses = 0

        for trade in trades:
            if trade.pnl > 0:
                consecutive_wins += 1
                consecutive_losses = 0
                max_consecutive_wins = max(max_consecutive_wins, consecutive_wins)
            else:
                consecutive_losses += 1
                consecutive_wins = 0
                max_consecutive_losses = max(max_consecutive_losses, consecutive_losses)

        result.max_consecutive_wins = max_consecutive_wins
        result.max_consecutive_losses = max_consecutive_losses

        return result
