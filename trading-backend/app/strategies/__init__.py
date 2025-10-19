"""
Trading Strategies Package

Implements TradingView Pine Script top-rated indicators in Python:
- SuperTrend (ATR-based trend following)
- RSI + EMA Crossover (Momentum + Trend)
- MACD + Stochastic RSI (Multi-confirmation)
- Ichimoku Cloud (Comprehensive trend system)
- WaveTrend Oscillator (Dead Zone strategy)
- LSTM AI (Deep learning + Technical + LLM ensemble)
"""

from .indicators import (
    calculate_supertrend,
    calculate_rsi,
    calculate_ema,
    calculate_macd,
    calculate_stochastic_rsi,
    calculate_ichimoku,
    calculate_wavetrend,
    calculate_atr
)

from .strategies import (
    SuperTrendStrategy,
    RSIEMAStrategy,
    MACDStochStrategy,
    IchimokuStrategy,
    WaveTrendStrategy,
    MultiIndicatorStrategy
)

from .lstm_strategy import (
    LSTMStrategy,
    LSTMFastStrategy,
    LSTMConservativeStrategy,
    LSTMAggressiveStrategy
)

__all__ = [
    'calculate_supertrend',
    'calculate_rsi',
    'calculate_ema',
    'calculate_macd',
    'calculate_stochastic_rsi',
    'calculate_ichimoku',
    'calculate_wavetrend',
    'calculate_atr',
    'SuperTrendStrategy',
    'RSIEMAStrategy',
    'MACDStochStrategy',
    'IchimokuStrategy',
    'WaveTrendStrategy',
    'MultiIndicatorStrategy',
    'LSTMStrategy',
    'LSTMFastStrategy',
    'LSTMConservativeStrategy',
    'LSTMAggressiveStrategy'
]
