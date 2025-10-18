"""
Backtesting Engine

Simulates trading strategies on historical data to evaluate performance.
"""

from .engine import BacktestEngine
from .metrics import PerformanceMetrics

__all__ = ['BacktestEngine', 'PerformanceMetrics']
