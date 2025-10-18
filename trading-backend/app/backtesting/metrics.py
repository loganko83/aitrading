"""
Performance Metrics Calculator

Calculates comprehensive performance metrics for backtesting results.
"""

import pandas as pd
import numpy as np
from typing import Dict, List
from dataclasses import dataclass


@dataclass
class PerformanceMetrics:
    """Performance metrics for strategy evaluation"""

    # Return metrics
    total_return: float
    total_return_pct: float
    annualized_return: float
    avg_return_per_trade: float

    # Risk metrics
    max_drawdown: float
    max_drawdown_pct: float
    volatility: float
    sharpe_ratio: float
    sortino_ratio: float
    calmar_ratio: float

    # Trade statistics
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float

    # Win/Loss analysis
    avg_win: float
    avg_loss: float
    profit_factor: float
    expectancy: float

    # Streak analysis
    max_consecutive_wins: int
    max_consecutive_losses: int

    # Time analysis
    avg_trade_duration: float  # in hours
    total_days: int

    @staticmethod
    def from_backtest_result(result) -> 'PerformanceMetrics':
        """Create PerformanceMetrics from BacktestResult"""

        # Calculate annualized return
        days = (result.end_date - result.start_date).days
        years = days / 365.25
        annualized_return = ((1 + result.total_return_pct / 100) ** (1 / years) - 1) * 100 if years > 0 else 0

        # Calculate volatility
        if len(result.equity_curve) > 1:
            returns = result.equity_curve.pct_change().dropna()
            volatility = returns.std() * np.sqrt(252)  # Annualized
        else:
            volatility = 0

        # Calculate Calmar ratio (return / max drawdown)
        calmar_ratio = annualized_return / result.max_drawdown_pct if result.max_drawdown_pct > 0 else 0

        # Calculate expectancy
        expectancy = (result.win_rate / 100 * result.avg_win) - ((100 - result.win_rate) / 100 * result.avg_loss)

        # Calculate average trade duration
        if result.trades:
            durations = [(t.exit_time - t.entry_time).total_seconds() / 3600
                        for t in result.trades if t.exit_time]
            avg_trade_duration = np.mean(durations) if durations else 0
        else:
            avg_trade_duration = 0

        return PerformanceMetrics(
            total_return=result.total_return,
            total_return_pct=result.total_return_pct,
            annualized_return=annualized_return,
            avg_return_per_trade=result.avg_return_per_trade,
            max_drawdown=result.max_drawdown,
            max_drawdown_pct=result.max_drawdown_pct,
            volatility=volatility,
            sharpe_ratio=result.sharpe_ratio,
            sortino_ratio=result.sortino_ratio,
            calmar_ratio=calmar_ratio,
            total_trades=result.total_trades,
            winning_trades=result.winning_trades,
            losing_trades=result.losing_trades,
            win_rate=result.win_rate,
            avg_win=result.avg_win,
            avg_loss=result.avg_loss,
            profit_factor=result.profit_factor,
            expectancy=expectancy,
            max_consecutive_wins=result.max_consecutive_wins,
            max_consecutive_losses=result.max_consecutive_losses,
            avg_trade_duration=avg_trade_duration,
            total_days=days
        )

    def to_dict(self) -> Dict:
        """Convert to dictionary for API response"""
        return {
            'returns': {
                'total': self.total_return,
                'total_pct': self.total_return_pct,
                'annualized_pct': self.annualized_return,
                'avg_per_trade': self.avg_return_per_trade
            },
            'risk': {
                'max_drawdown': self.max_drawdown,
                'max_drawdown_pct': self.max_drawdown_pct,
                'volatility': self.volatility,
                'sharpe_ratio': self.sharpe_ratio,
                'sortino_ratio': self.sortino_ratio,
                'calmar_ratio': self.calmar_ratio
            },
            'trades': {
                'total': self.total_trades,
                'winning': self.winning_trades,
                'losing': self.losing_trades,
                'win_rate_pct': self.win_rate
            },
            'analysis': {
                'avg_win': self.avg_win,
                'avg_loss': self.avg_loss,
                'profit_factor': self.profit_factor,
                'expectancy': self.expectancy,
                'max_consecutive_wins': self.max_consecutive_wins,
                'max_consecutive_losses': self.max_consecutive_losses
            },
            'timing': {
                'avg_trade_duration_hours': self.avg_trade_duration,
                'total_days': self.total_days
            }
        }

    def get_rating(self) -> str:
        """
        Get strategy rating based on performance metrics

        Rating criteria:
        - Excellent: Sharpe > 2, Win rate > 60%, Profit factor > 2
        - Good: Sharpe > 1, Win rate > 50%, Profit factor > 1.5
        - Average: Sharpe > 0.5, Win rate > 40%, Profit factor > 1
        - Poor: Below average thresholds
        """
        if (self.sharpe_ratio > 2 and
            self.win_rate > 60 and
            self.profit_factor > 2):
            return "EXCELLENT"
        elif (self.sharpe_ratio > 1 and
              self.win_rate > 50 and
              self.profit_factor > 1.5):
            return "GOOD"
        elif (self.sharpe_ratio > 0.5 and
              self.win_rate > 40 and
              self.profit_factor > 1):
            return "AVERAGE"
        else:
            return "POOR"
