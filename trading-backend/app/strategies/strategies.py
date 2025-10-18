"""
Trading Strategy Classes

Implements TradingView top-rated strategies as Python classes:
1. SuperTrend Strategy (67% win rate, 177% returns reported)
2. RSI + EMA Crossover Strategy
3. MACD + Stochastic RSI Multi-Confirmation Strategy
4. Ichimoku Cloud Strategy
5. WaveTrend Dead Zone Strategy
6. Multi-Indicator Combined Strategy

Each strategy generates buy/sell signals based on technical indicators.
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional, Tuple
from dataclasses import dataclass
import logging

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

logger = logging.getLogger(__name__)


@dataclass
class Signal:
    """Trading Signal Output"""
    should_enter: bool
    direction: str  # 'LONG' or 'SHORT'
    confidence: float  # 0.0 to 1.0
    entry_price: float
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    reasoning: str = ""
    indicator_values: Dict = None


class BaseStrategy:
    """Base class for all trading strategies"""

    def __init__(self, name: str):
        self.name = name

    def generate_signal(self, df: pd.DataFrame, current_price: float) -> Signal:
        """
        Generate trading signal based on strategy logic

        Args:
            df: DataFrame with OHLC data and indicators
            current_price: Current market price

        Returns:
            Signal object with entry decision and levels
        """
        raise NotImplementedError("Subclasses must implement generate_signal()")

    def calculate_stop_loss_take_profit(
        self,
        entry_price: float,
        direction: str,
        atr: float,
        atr_multiplier_sl: float = 1.5,
        atr_multiplier_tp: float = 3.0
    ) -> Tuple[float, float]:
        """
        Calculate dynamic stop-loss and take-profit using ATR

        Args:
            entry_price: Entry price
            direction: 'LONG' or 'SHORT'
            atr: Average True Range value
            atr_multiplier_sl: ATR multiplier for stop-loss (default 1.5)
            atr_multiplier_tp: ATR multiplier for take-profit (default 3.0)

        Returns:
            Tuple of (stop_loss, take_profit)
        """
        if direction == 'LONG':
            stop_loss = entry_price - (atr * atr_multiplier_sl)
            take_profit = entry_price + (atr * atr_multiplier_tp)
        else:  # SHORT
            stop_loss = entry_price + (atr * atr_multiplier_sl)
            take_profit = entry_price - (atr * atr_multiplier_tp)

        return stop_loss, take_profit


class SuperTrendStrategy(BaseStrategy):
    """
    SuperTrend Strategy

    Based on TradingView's top-rated SuperTrend indicator.
    Reported performance: 67% win rate, 177% returns in live trading (Feb 2025).

    Entry Rules:
        - LONG: SuperTrend direction changes from -1 to 1 (bearish to bullish)
        - SHORT: SuperTrend direction changes from 1 to -1 (bullish to bearish)

    Exit Rules:
        - Reverse signal or ATR-based stop-loss/take-profit
    """

    def __init__(
        self,
        period: int = 10,
        multiplier: float = 3.0,
        atr_sl_multiplier: float = 1.5,
        atr_tp_multiplier: float = 3.0
    ):
        super().__init__("SuperTrend")
        self.period = period
        self.multiplier = multiplier
        self.atr_sl_multiplier = atr_sl_multiplier
        self.atr_tp_multiplier = atr_tp_multiplier

    def generate_signal(self, df: pd.DataFrame, current_price: float) -> Signal:
        """Generate SuperTrend signal"""

        # Calculate SuperTrend
        supertrend, direction = calculate_supertrend(
            df, period=self.period, multiplier=self.multiplier
        )

        # Calculate ATR for stop-loss/take-profit
        atr = calculate_atr(df, period=self.period)

        # Get latest values
        current_direction = direction.iloc[-1]
        prev_direction = direction.iloc[-2] if len(direction) > 1 else current_direction
        current_atr = atr.iloc[-1]

        # Check for direction change (signal)
        should_enter = False
        trade_direction = None
        confidence = 0.0
        reasoning = ""

        if prev_direction == -1 and current_direction == 1:
            # Bullish signal
            should_enter = True
            trade_direction = 'LONG'
            confidence = 0.75
            reasoning = "SuperTrend bullish reversal: Direction changed from -1 to 1"

        elif prev_direction == 1 and current_direction == -1:
            # Bearish signal
            should_enter = True
            trade_direction = 'SHORT'
            confidence = 0.75
            reasoning = "SuperTrend bearish reversal: Direction changed from 1 to -1"

        # Calculate stop-loss and take-profit if signal exists
        stop_loss = None
        take_profit = None

        if should_enter and trade_direction:
            stop_loss, take_profit = self.calculate_stop_loss_take_profit(
                current_price,
                trade_direction,
                current_atr,
                self.atr_sl_multiplier,
                self.atr_tp_multiplier
            )

        return Signal(
            should_enter=should_enter,
            direction=trade_direction if should_enter else 'NEUTRAL',
            confidence=confidence,
            entry_price=current_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            reasoning=reasoning,
            indicator_values={
                'supertrend': supertrend.iloc[-1],
                'direction': current_direction,
                'atr': current_atr
            }
        )


class RSIEMAStrategy(BaseStrategy):
    """
    RSI + EMA Crossover Strategy

    Combines momentum (RSI) with trend confirmation (EMA) for high-probability entries.

    Entry Rules:
        LONG:
            - RSI > 30 (not oversold, momentum building)
            - Price crosses above EMA20
            - EMA20 > EMA50 (uptrend confirmation)

        SHORT:
            - RSI < 70 (not overbought, momentum weakening)
            - Price crosses below EMA20
            - EMA20 < EMA50 (downtrend confirmation)
    """

    def __init__(
        self,
        rsi_period: int = 14,
        ema_fast: int = 20,
        ema_slow: int = 50,
        rsi_oversold: int = 30,
        rsi_overbought: int = 70,
        atr_period: int = 14
    ):
        super().__init__("RSI+EMA")
        self.rsi_period = rsi_period
        self.ema_fast = ema_fast
        self.ema_slow = ema_slow
        self.rsi_oversold = rsi_oversold
        self.rsi_overbought = rsi_overbought
        self.atr_period = atr_period

    def generate_signal(self, df: pd.DataFrame, current_price: float) -> Signal:
        """Generate RSI+EMA signal"""

        # Calculate indicators
        rsi = calculate_rsi(df, period=self.rsi_period)
        ema20 = calculate_ema(df, period=self.ema_fast)
        ema50 = calculate_ema(df, period=self.ema_slow)
        atr = calculate_atr(df, period=self.atr_period)

        # Get latest values
        current_rsi = rsi.iloc[-1]
        current_ema20 = ema20.iloc[-1]
        current_ema50 = ema50.iloc[-1]
        prev_close = df['close'].iloc[-2]
        prev_ema20 = ema20.iloc[-2]
        current_atr = atr.iloc[-1]

        # Initialize signal
        should_enter = False
        trade_direction = None
        confidence = 0.0
        reasoning = ""

        # Check for LONG signal
        if (current_rsi > self.rsi_oversold and
            prev_close < prev_ema20 and current_price > current_ema20 and
            current_ema20 > current_ema50):

            should_enter = True
            trade_direction = 'LONG'

            # Calculate confidence based on RSI and EMA separation
            rsi_strength = min((current_rsi - self.rsi_oversold) / 40, 1.0)
            ema_separation = (current_ema20 - current_ema50) / current_ema50
            confidence = 0.5 + (rsi_strength * 0.2) + min(ema_separation * 10, 0.3)

            reasoning = (
                f"RSI+EMA LONG: RSI={current_rsi:.1f}, "
                f"Price crossed above EMA20, EMA20 > EMA50 (uptrend)"
            )

        # Check for SHORT signal
        elif (current_rsi < self.rsi_overbought and
              prev_close > prev_ema20 and current_price < current_ema20 and
              current_ema20 < current_ema50):

            should_enter = True
            trade_direction = 'SHORT'

            # Calculate confidence
            rsi_strength = min((self.rsi_overbought - current_rsi) / 40, 1.0)
            ema_separation = (current_ema50 - current_ema20) / current_ema50
            confidence = 0.5 + (rsi_strength * 0.2) + min(ema_separation * 10, 0.3)

            reasoning = (
                f"RSI+EMA SHORT: RSI={current_rsi:.1f}, "
                f"Price crossed below EMA20, EMA20 < EMA50 (downtrend)"
            )

        # Calculate stop-loss and take-profit
        stop_loss = None
        take_profit = None

        if should_enter and trade_direction:
            stop_loss, take_profit = self.calculate_stop_loss_take_profit(
                current_price, trade_direction, current_atr
            )

        return Signal(
            should_enter=should_enter,
            direction=trade_direction if should_enter else 'NEUTRAL',
            confidence=confidence,
            entry_price=current_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            reasoning=reasoning,
            indicator_values={
                'rsi': current_rsi,
                'ema20': current_ema20,
                'ema50': current_ema50,
                'atr': current_atr
            }
        )


class MACDStochStrategy(BaseStrategy):
    """
    MACD + Stochastic RSI Multi-Confirmation Strategy

    Combines momentum divergence (MACD) with overbought/oversold detection (Stochastic RSI).
    Multi-layer filtering reduces false signals.

    Entry Rules:
        LONG:
            - MACD line crosses above Signal line (bullish)
            - Stochastic RSI %K crosses above %D
            - Stochastic RSI < 80 (not overbought)

        SHORT:
            - MACD line crosses below Signal line (bearish)
            - Stochastic RSI %K crosses below %D
            - Stochastic RSI > 20 (not oversold)
    """

    def __init__(
        self,
        macd_fast: int = 12,
        macd_slow: int = 26,
        macd_signal: int = 9,
        stoch_rsi_period: int = 14,
        stoch_period: int = 14,
        atr_period: int = 14
    ):
        super().__init__("MACD+StochRSI")
        self.macd_fast = macd_fast
        self.macd_slow = macd_slow
        self.macd_signal = macd_signal
        self.stoch_rsi_period = stoch_rsi_period
        self.stoch_period = stoch_period
        self.atr_period = atr_period

    def generate_signal(self, df: pd.DataFrame, current_price: float) -> Signal:
        """Generate MACD+StochRSI signal"""

        # Calculate indicators
        macd_line, signal_line, histogram = calculate_macd(
            df, self.macd_fast, self.macd_slow, self.macd_signal
        )
        stoch_k, stoch_d = calculate_stochastic_rsi(
            df, self.stoch_rsi_period, self.stoch_period
        )
        atr = calculate_atr(df, period=self.atr_period)

        # Get latest values
        current_macd = macd_line.iloc[-1]
        current_signal = signal_line.iloc[-1]
        prev_macd = macd_line.iloc[-2]
        prev_signal = signal_line.iloc[-2]

        current_stoch_k = stoch_k.iloc[-1]
        current_stoch_d = stoch_d.iloc[-1]
        prev_stoch_k = stoch_k.iloc[-2]
        prev_stoch_d = stoch_d.iloc[-2]

        current_atr = atr.iloc[-1]

        # Initialize signal
        should_enter = False
        trade_direction = None
        confidence = 0.0
        reasoning = ""

        # Check for LONG signal
        macd_bullish_cross = prev_macd < prev_signal and current_macd > current_signal
        stoch_bullish_cross = prev_stoch_k < prev_stoch_d and current_stoch_k > current_stoch_d

        if macd_bullish_cross and stoch_bullish_cross and current_stoch_k < 80:
            should_enter = True
            trade_direction = 'LONG'

            # Calculate confidence based on indicator strength
            macd_strength = min(abs(current_macd - current_signal) / abs(current_signal), 0.3)
            stoch_position = (80 - current_stoch_k) / 80  # Lower is better for long
            confidence = 0.6 + macd_strength + (stoch_position * 0.1)

            reasoning = (
                f"MACD+Stoch LONG: MACD bullish cross, "
                f"Stoch %K crossed above %D (K={current_stoch_k:.1f})"
            )

        # Check for SHORT signal
        macd_bearish_cross = prev_macd > prev_signal and current_macd < current_signal
        stoch_bearish_cross = prev_stoch_k > prev_stoch_d and current_stoch_k < current_stoch_d

        elif macd_bearish_cross and stoch_bearish_cross and current_stoch_k > 20:
            should_enter = True
            trade_direction = 'SHORT'

            # Calculate confidence
            macd_strength = min(abs(current_signal - current_macd) / abs(current_signal), 0.3)
            stoch_position = current_stoch_k / 80  # Higher is better for short
            confidence = 0.6 + macd_strength + (stoch_position * 0.1)

            reasoning = (
                f"MACD+Stoch SHORT: MACD bearish cross, "
                f"Stoch %K crossed below %D (K={current_stoch_k:.1f})"
            )

        # Calculate stop-loss and take-profit
        stop_loss = None
        take_profit = None

        if should_enter and trade_direction:
            stop_loss, take_profit = self.calculate_stop_loss_take_profit(
                current_price, trade_direction, current_atr
            )

        return Signal(
            should_enter=should_enter,
            direction=trade_direction if should_enter else 'NEUTRAL',
            confidence=confidence,
            entry_price=current_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            reasoning=reasoning,
            indicator_values={
                'macd': current_macd,
                'macd_signal': current_signal,
                'stoch_k': current_stoch_k,
                'stoch_d': current_stoch_d,
                'atr': current_atr
            }
        )


class IchimokuStrategy(BaseStrategy):
    """
    Ichimoku Cloud Strategy

    Comprehensive trend-following system. One of the most profitable strategies with clear signals.

    Entry Rules:
        LONG:
            - Price crosses above cloud (Senkou Span A & B)
            - Tenkan-sen crosses above Kijun-sen (golden cross)
            - Chikou Span above price (26 periods ago)

        SHORT:
            - Price crosses below cloud
            - Tenkan-sen crosses below Kijun-sen (death cross)
            - Chikou Span below price (26 periods ago)
    """

    def __init__(
        self,
        tenkan_period: int = 9,
        kijun_period: int = 26,
        senkou_b_period: int = 52,
        atr_period: int = 14
    ):
        super().__init__("Ichimoku")
        self.tenkan_period = tenkan_period
        self.kijun_period = kijun_period
        self.senkou_b_period = senkou_b_period
        self.atr_period = atr_period

    def generate_signal(self, df: pd.DataFrame, current_price: float) -> Signal:
        """Generate Ichimoku signal"""

        # Calculate Ichimoku
        ichimoku = calculate_ichimoku(
            df, self.tenkan_period, self.kijun_period, self.senkou_b_period
        )
        atr = calculate_atr(df, period=self.atr_period)

        # Get latest values
        tenkan = ichimoku['tenkan_sen'].iloc[-1]
        kijun = ichimoku['kijun_sen'].iloc[-1]
        senkou_a = ichimoku['senkou_span_a'].iloc[-1]
        senkou_b = ichimoku['senkou_span_b'].iloc[-1]

        prev_tenkan = ichimoku['tenkan_sen'].iloc[-2]
        prev_kijun = ichimoku['kijun_sen'].iloc[-2]

        current_atr = atr.iloc[-1]

        # Cloud boundaries
        cloud_top = max(senkou_a, senkou_b)
        cloud_bottom = min(senkou_a, senkou_b)

        # Initialize signal
        should_enter = False
        trade_direction = None
        confidence = 0.0
        reasoning = ""

        # Check for LONG signal
        tenkan_bullish_cross = prev_tenkan < prev_kijun and tenkan > kijun
        price_above_cloud = current_price > cloud_top

        if tenkan_bullish_cross and price_above_cloud:
            should_enter = True
            trade_direction = 'LONG'

            # Calculate confidence based on cloud thickness and distance
            cloud_thickness = (cloud_top - cloud_bottom) / cloud_bottom
            price_distance = (current_price - cloud_top) / cloud_top

            confidence = 0.7 + min(cloud_thickness * 5, 0.15) + min(price_distance * 10, 0.15)

            reasoning = (
                f"Ichimoku LONG: Tenkan crossed above Kijun, "
                f"Price above cloud ({current_price:.2f} > {cloud_top:.2f})"
            )

        # Check for SHORT signal
        tenkan_bearish_cross = prev_tenkan > prev_kijun and tenkan < kijun
        price_below_cloud = current_price < cloud_bottom

        elif tenkan_bearish_cross and price_below_cloud:
            should_enter = True
            trade_direction = 'SHORT'

            # Calculate confidence
            cloud_thickness = (cloud_top - cloud_bottom) / cloud_bottom
            price_distance = (cloud_bottom - current_price) / cloud_bottom

            confidence = 0.7 + min(cloud_thickness * 5, 0.15) + min(price_distance * 10, 0.15)

            reasoning = (
                f"Ichimoku SHORT: Tenkan crossed below Kijun, "
                f"Price below cloud ({current_price:.2f} < {cloud_bottom:.2f})"
            )

        # Calculate stop-loss and take-profit
        stop_loss = None
        take_profit = None

        if should_enter and trade_direction:
            stop_loss, take_profit = self.calculate_stop_loss_take_profit(
                current_price, trade_direction, current_atr, atr_multiplier_sl=2.0
            )

        return Signal(
            should_enter=should_enter,
            direction=trade_direction if should_enter else 'NEUTRAL',
            confidence=confidence,
            entry_price=current_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            reasoning=reasoning,
            indicator_values={
                'tenkan_sen': tenkan,
                'kijun_sen': kijun,
                'cloud_top': cloud_top,
                'cloud_bottom': cloud_bottom,
                'atr': current_atr
            }
        )


class WaveTrendStrategy(BaseStrategy):
    """
    WaveTrend Dead Zone Strategy

    Uses WaveTrend oscillator to identify "dead zones" and capitalize on breakouts.
    Quietly profitable for 2+ years according to TradingView analysis.

    Entry Rules:
        LONG:
            - WT1 crosses above WT2
            - WT1 < -40 (oversold zone)

        SHORT:
            - WT1 crosses below WT2
            - WT1 > 40 (overbought zone)
    """

    def __init__(
        self,
        channel_length: int = 10,
        average_length: int = 21,
        oversold: float = -60,
        overbought: float = 60,
        atr_period: int = 14
    ):
        super().__init__("WaveTrend")
        self.channel_length = channel_length
        self.average_length = average_length
        self.oversold = oversold
        self.overbought = overbought
        self.atr_period = atr_period

    def generate_signal(self, df: pd.DataFrame, current_price: float) -> Signal:
        """Generate WaveTrend signal"""

        # Calculate indicators
        wt1, wt2 = calculate_wavetrend(df, self.channel_length, self.average_length)
        atr = calculate_atr(df, period=self.atr_period)

        # Get latest values
        current_wt1 = wt1.iloc[-1]
        current_wt2 = wt2.iloc[-1]
        prev_wt1 = wt1.iloc[-2]
        prev_wt2 = wt2.iloc[-2]

        current_atr = atr.iloc[-1]

        # Initialize signal
        should_enter = False
        trade_direction = None
        confidence = 0.0
        reasoning = ""

        # Check for LONG signal (bullish cross in oversold zone)
        wt_bullish_cross = prev_wt1 < prev_wt2 and current_wt1 > current_wt2

        if wt_bullish_cross and current_wt1 < -40:
            should_enter = True
            trade_direction = 'LONG'

            # Confidence based on oversold depth
            oversold_depth = max(0, (-60 - current_wt1) / 40)
            confidence = 0.65 + min(oversold_depth * 0.3, 0.3)

            reasoning = (
                f"WaveTrend LONG: WT1 crossed above WT2 in oversold zone "
                f"(WT1={current_wt1:.1f})"
            )

        # Check for SHORT signal (bearish cross in overbought zone)
        wt_bearish_cross = prev_wt1 > prev_wt2 and current_wt1 < current_wt2

        elif wt_bearish_cross and current_wt1 > 40:
            should_enter = True
            trade_direction = 'SHORT'

            # Confidence based on overbought depth
            overbought_depth = max(0, (current_wt1 - 60) / 40)
            confidence = 0.65 + min(overbought_depth * 0.3, 0.3)

            reasoning = (
                f"WaveTrend SHORT: WT1 crossed below WT2 in overbought zone "
                f"(WT1={current_wt1:.1f})"
            )

        # Calculate stop-loss and take-profit
        stop_loss = None
        take_profit = None

        if should_enter and trade_direction:
            stop_loss, take_profit = self.calculate_stop_loss_take_profit(
                current_price, trade_direction, current_atr
            )

        return Signal(
            should_enter=should_enter,
            direction=trade_direction if should_enter else 'NEUTRAL',
            confidence=confidence,
            entry_price=current_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            reasoning=reasoning,
            indicator_values={
                'wt1': current_wt1,
                'wt2': current_wt2,
                'atr': current_atr
            }
        )


class MultiIndicatorStrategy(BaseStrategy):
    """
    Multi-Indicator Combined Strategy

    Combines multiple strategies for consensus-based signals.
    Reduces false positives by requiring agreement across indicators.

    Uses:
        - SuperTrend (trend direction)
        - RSI (momentum)
        - MACD (trend strength)

    Entry Rules:
        - Minimum 2 out of 3 strategies must agree
        - Confidence weighted by agreement level
    """

    def __init__(self, min_agreement: int = 2):
        super().__init__("MultiIndicator")
        self.min_agreement = min_agreement

        # Initialize sub-strategies
        self.supertrend = SuperTrendStrategy()
        self.rsi_ema = RSIEMAStrategy()
        self.macd_stoch = MACDStochStrategy()

    def generate_signal(self, df: pd.DataFrame, current_price: float) -> Signal:
        """Generate multi-indicator consensus signal"""

        # Get signals from all strategies
        st_signal = self.supertrend.generate_signal(df, current_price)
        rsi_signal = self.rsi_ema.generate_signal(df, current_price)
        macd_signal = self.macd_stoch.generate_signal(df, current_price)

        signals = [st_signal, rsi_signal, macd_signal]

        # Count votes for each direction
        long_votes = sum(1 for s in signals if s.should_enter and s.direction == 'LONG')
        short_votes = sum(1 for s in signals if s.should_enter and s.direction == 'SHORT')

        # Determine consensus
        should_enter = False
        trade_direction = None
        confidence = 0.0
        reasoning_parts = []

        if long_votes >= self.min_agreement:
            should_enter = True
            trade_direction = 'LONG'
            confidence = sum(s.confidence for s in signals if s.should_enter and s.direction == 'LONG') / long_votes
            reasoning_parts = [s.reasoning for s in signals if s.should_enter and s.direction == 'LONG']

        elif short_votes >= self.min_agreement:
            should_enter = True
            trade_direction = 'SHORT'
            confidence = sum(s.confidence for s in signals if s.should_enter and s.direction == 'SHORT') / short_votes
            reasoning_parts = [s.reasoning for s in signals if s.should_enter and s.direction == 'SHORT']

        # Calculate ATR for SL/TP
        atr = calculate_atr(df, period=14)
        current_atr = atr.iloc[-1]

        # Calculate stop-loss and take-profit
        stop_loss = None
        take_profit = None

        if should_enter and trade_direction:
            stop_loss, take_profit = self.calculate_stop_loss_take_profit(
                current_price, trade_direction, current_atr
            )

        reasoning = (
            f"Multi-Indicator {trade_direction if should_enter else 'NEUTRAL'}: "
            f"{long_votes if trade_direction == 'LONG' else short_votes}/3 strategies agree. "
            + " | ".join(reasoning_parts)
        )

        return Signal(
            should_enter=should_enter,
            direction=trade_direction if should_enter else 'NEUTRAL',
            confidence=confidence,
            entry_price=current_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            reasoning=reasoning,
            indicator_values={
                'long_votes': long_votes,
                'short_votes': short_votes,
                'atr': current_atr
            }
        )
