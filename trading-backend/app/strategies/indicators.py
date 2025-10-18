"""
Technical Indicators - TradingView Pine Script Implementations in Python

Based on top-rated TradingView indicators:
- SuperTrend: ATR-based trend following (67% win rate in live trading)
- RSI: Relative Strength Index for overbought/oversold
- EMA: Exponential Moving Average for trend confirmation
- MACD: Moving Average Convergence Divergence for momentum
- Stochastic RSI: Enhanced RSI for reversal detection
- Ichimoku Cloud: Comprehensive trend system
- WaveTrend: Oscillator for dead zone strategy
- ATR: Average True Range for volatility measurement
"""

import pandas as pd
import numpy as np
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)


def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """
    Calculate Average True Range (ATR)

    ATR measures market volatility by decomposing the entire range of an asset price.
    Used by SuperTrend and for dynamic stop-loss/take-profit levels.

    Args:
        df: DataFrame with 'high', 'low', 'close' columns
        period: ATR period (default 14)

    Returns:
        ATR values as pandas Series

    Example:
        >>> df['atr'] = calculate_atr(df, period=14)
    """
    high = df['high']
    low = df['low']
    close = df['close']

    # True Range = max(high - low, abs(high - prev_close), abs(low - prev_close))
    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low - close.shift(1))

    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

    # ATR = EMA of True Range
    atr = tr.ewm(span=period, adjust=False).mean()

    return atr


def calculate_supertrend(
    df: pd.DataFrame,
    period: int = 10,
    multiplier: float = 3.0
) -> Tuple[pd.Series, pd.Series]:
    """
    Calculate SuperTrend Indicator

    SuperTrend is a trend-following indicator that uses ATR to plot dynamic support/resistance.
    Highly effective in Bitcoin/crypto markets with 67% win rate reported in live trading.

    Formula:
        Basic Upper Band = (High + Low) / 2 + (Multiplier × ATR)
        Basic Lower Band = (High + Low) / 2 - (Multiplier × ATR)

    Args:
        df: DataFrame with OHLC data
        period: ATR period (default 10)
        multiplier: ATR multiplier (default 3.0, higher = less sensitive)

    Returns:
        Tuple of (supertrend, direction)
        - supertrend: SuperTrend line values
        - direction: 1 for bullish (green), -1 for bearish (red)

    Example:
        >>> df['supertrend'], df['st_direction'] = calculate_supertrend(df)
        >>> # Buy when direction changes from -1 to 1
        >>> # Sell when direction changes from 1 to -1
    """
    high = df['high']
    low = df['low']
    close = df['close']

    # Calculate ATR
    atr = calculate_atr(df, period=period)

    # Calculate basic bands
    hl_avg = (high + low) / 2
    upper_band = hl_avg + (multiplier * atr)
    lower_band = hl_avg - (multiplier * atr)

    # Initialize SuperTrend
    supertrend = pd.Series(index=df.index, dtype=float)
    direction = pd.Series(index=df.index, dtype=int)

    # First value
    supertrend.iloc[0] = lower_band.iloc[0]
    direction.iloc[0] = 1

    # Calculate SuperTrend
    for i in range(1, len(df)):
        # Update bands based on previous values
        if close.iloc[i] > upper_band.iloc[i-1]:
            direction.iloc[i] = 1
        elif close.iloc[i] < lower_band.iloc[i-1]:
            direction.iloc[i] = -1
        else:
            direction.iloc[i] = direction.iloc[i-1]

            # Adjust bands
            if direction.iloc[i] == 1 and lower_band.iloc[i] < lower_band.iloc[i-1]:
                lower_band.iloc[i] = lower_band.iloc[i-1]
            if direction.iloc[i] == -1 and upper_band.iloc[i] > upper_band.iloc[i-1]:
                upper_band.iloc[i] = upper_band.iloc[i-1]

        # Set SuperTrend value
        if direction.iloc[i] == 1:
            supertrend.iloc[i] = lower_band.iloc[i]
        else:
            supertrend.iloc[i] = upper_band.iloc[i]

    return supertrend, direction


def calculate_rsi(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """
    Calculate Relative Strength Index (RSI)

    RSI measures the magnitude of recent price changes to evaluate overbought/oversold conditions.

    Formula:
        RSI = 100 - (100 / (1 + RS))
        RS = Average Gain / Average Loss

    Args:
        df: DataFrame with 'close' column
        period: RSI period (default 14)

    Returns:
        RSI values (0-100)

    Interpretation:
        > 70: Overbought (potential sell signal)
        < 30: Oversold (potential buy signal)

    Example:
        >>> df['rsi'] = calculate_rsi(df, period=14)
    """
    close = df['close']

    # Calculate price changes
    delta = close.diff()

    # Separate gains and losses
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)

    # Calculate average gain and loss using EMA
    avg_gain = gain.ewm(span=period, adjust=False).mean()
    avg_loss = loss.ewm(span=period, adjust=False).mean()

    # Calculate RS and RSI
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))

    return rsi


def calculate_ema(df: pd.DataFrame, period: int) -> pd.Series:
    """
    Calculate Exponential Moving Average (EMA)

    EMA gives more weight to recent prices, making it more responsive than SMA.

    Args:
        df: DataFrame with 'close' column
        period: EMA period

    Returns:
        EMA values

    Example:
        >>> df['ema20'] = calculate_ema(df, period=20)
        >>> df['ema50'] = calculate_ema(df, period=50)
    """
    return df['close'].ewm(span=period, adjust=False).mean()


def calculate_macd(
    df: pd.DataFrame,
    fast_period: int = 12,
    slow_period: int = 26,
    signal_period: int = 9
) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """
    Calculate MACD (Moving Average Convergence Divergence)

    MACD shows the relationship between two moving averages and is used to identify trend changes.

    Formula:
        MACD Line = EMA(12) - EMA(26)
        Signal Line = EMA(9) of MACD Line
        Histogram = MACD Line - Signal Line

    Args:
        df: DataFrame with 'close' column
        fast_period: Fast EMA period (default 12)
        slow_period: Slow EMA period (default 26)
        signal_period: Signal line period (default 9)

    Returns:
        Tuple of (macd_line, signal_line, histogram)

    Signals:
        - Bullish: MACD crosses above signal line
        - Bearish: MACD crosses below signal line

    Example:
        >>> macd, signal, histogram = calculate_macd(df)
    """
    close = df['close']

    # Calculate MACD line
    ema_fast = close.ewm(span=fast_period, adjust=False).mean()
    ema_slow = close.ewm(span=slow_period, adjust=False).mean()
    macd_line = ema_fast - ema_slow

    # Calculate signal line
    signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()

    # Calculate histogram
    histogram = macd_line - signal_line

    return macd_line, signal_line, histogram


def calculate_stochastic_rsi(
    df: pd.DataFrame,
    rsi_period: int = 14,
    stoch_period: int = 14,
    k_period: int = 3,
    d_period: int = 3
) -> Tuple[pd.Series, pd.Series]:
    """
    Calculate Stochastic RSI

    Stochastic RSI applies Stochastic oscillator formula to RSI values,
    making it more sensitive for identifying overbought/oversold conditions.
    Excels in ranging markets for reversal detection.

    Formula:
        StochRSI = (RSI - RSI_min) / (RSI_max - RSI_min)
        %K = SMA(StochRSI, k_period)
        %D = SMA(%K, d_period)

    Args:
        df: DataFrame with 'close' column
        rsi_period: RSI calculation period (default 14)
        stoch_period: Stochastic lookback period (default 14)
        k_period: %K smoothing period (default 3)
        d_period: %D smoothing period (default 3)

    Returns:
        Tuple of (%K, %D) both ranging 0-100

    Signals:
        > 80: Overbought
        < 20: Oversold
        %K crosses above %D: Buy signal
        %K crosses below %D: Sell signal

    Example:
        >>> stoch_k, stoch_d = calculate_stochastic_rsi(df)
    """
    # Calculate RSI
    rsi = calculate_rsi(df, period=rsi_period)

    # Calculate Stochastic of RSI
    rsi_min = rsi.rolling(window=stoch_period).min()
    rsi_max = rsi.rolling(window=stoch_period).max()

    stoch_rsi = (rsi - rsi_min) / (rsi_max - rsi_min) * 100

    # Calculate %K and %D
    stoch_k = stoch_rsi.rolling(window=k_period).mean()
    stoch_d = stoch_k.rolling(window=d_period).mean()

    return stoch_k, stoch_d


def calculate_ichimoku(
    df: pd.DataFrame,
    tenkan_period: int = 9,
    kijun_period: int = 26,
    senkou_b_period: int = 52,
    displacement: int = 26
) -> dict:
    """
    Calculate Ichimoku Cloud

    Ichimoku is a comprehensive indicator that shows support/resistance, momentum, and trend direction.
    One of the most profitable strategies with clear buy/sell signals.

    Components:
        - Tenkan-sen (Conversion Line): (9-period high + 9-period low) / 2
        - Kijun-sen (Base Line): (26-period high + 26-period low) / 2
        - Senkou Span A (Leading Span A): (Tenkan-sen + Kijun-sen) / 2, shifted 26 periods ahead
        - Senkou Span B (Leading Span B): (52-period high + 52-period low) / 2, shifted 26 periods ahead
        - Chikou Span (Lagging Span): Close price shifted 26 periods back

    Args:
        df: DataFrame with OHLC data
        tenkan_period: Conversion line period (default 9)
        kijun_period: Base line period (default 26)
        senkou_b_period: Leading Span B period (default 52)
        displacement: Cloud shift periods (default 26)

    Returns:
        Dictionary with all Ichimoku components

    Signals:
        - Buy: Price crosses above cloud, Tenkan crosses above Kijun
        - Sell: Price crosses below cloud, Tenkan crosses below Kijun
        - Strong trend: Cloud is thick
        - Weak trend: Cloud is thin

    Example:
        >>> ichimoku = calculate_ichimoku(df)
        >>> df['tenkan'] = ichimoku['tenkan_sen']
        >>> df['kijun'] = ichimoku['kijun_sen']
    """
    high = df['high']
    low = df['low']
    close = df['close']

    # Tenkan-sen (Conversion Line)
    tenkan_high = high.rolling(window=tenkan_period).max()
    tenkan_low = low.rolling(window=tenkan_period).min()
    tenkan_sen = (tenkan_high + tenkan_low) / 2

    # Kijun-sen (Base Line)
    kijun_high = high.rolling(window=kijun_period).max()
    kijun_low = low.rolling(window=kijun_period).min()
    kijun_sen = (kijun_high + kijun_low) / 2

    # Senkou Span A (Leading Span A)
    senkou_span_a = ((tenkan_sen + kijun_sen) / 2).shift(displacement)

    # Senkou Span B (Leading Span B)
    senkou_high = high.rolling(window=senkou_b_period).max()
    senkou_low = low.rolling(window=senkou_b_period).min()
    senkou_span_b = ((senkou_high + senkou_low) / 2).shift(displacement)

    # Chikou Span (Lagging Span)
    chikou_span = close.shift(-displacement)

    return {
        'tenkan_sen': tenkan_sen,
        'kijun_sen': kijun_sen,
        'senkou_span_a': senkou_span_a,
        'senkou_span_b': senkou_span_b,
        'chikou_span': chikou_span
    }


def calculate_wavetrend(
    df: pd.DataFrame,
    channel_length: int = 10,
    average_length: int = 21,
    ma_length: int = 4
) -> Tuple[pd.Series, pd.Series]:
    """
    Calculate WaveTrend Oscillator

    WaveTrend identifies overbought/oversold conditions and potential reversals.
    Used in the "Dead Zone" strategy with 2+ years of profitability.

    Formula (simplified):
        AP = (High + Low + Close) / 3
        ESA = EMA(AP, channel_length)
        D = EMA(abs(AP - ESA), channel_length)
        CI = (AP - ESA) / (0.015 × D)
        WT1 = EMA(CI, average_length)
        WT2 = SMA(WT1, ma_length)

    Args:
        df: DataFrame with OHLC data
        channel_length: Channel period (default 10)
        average_length: Average period (default 21)
        ma_length: Moving average period (default 4)

    Returns:
        Tuple of (wt1, wt2)

    Signals:
        > 60: Overbought
        < -60: Oversold
        WT1 crosses above WT2: Buy signal
        WT1 crosses below WT2: Sell signal

    Example:
        >>> wt1, wt2 = calculate_wavetrend(df)
    """
    high = df['high']
    low = df['low']
    close = df['close']

    # Average Price
    ap = (high + low + close) / 3

    # ESA (Exponential Moving Average)
    esa = ap.ewm(span=channel_length, adjust=False).mean()

    # D (Deviation)
    d = abs(ap - esa).ewm(span=channel_length, adjust=False).mean()

    # CI (Channel Index)
    ci = (ap - esa) / (0.015 * d)

    # WT1 (WaveTrend 1)
    wt1 = ci.ewm(span=average_length, adjust=False).mean()

    # WT2 (WaveTrend 2)
    wt2 = wt1.rolling(window=ma_length).mean()

    return wt1, wt2
