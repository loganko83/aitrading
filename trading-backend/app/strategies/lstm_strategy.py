"""
LSTM AI Strategy

AI-powered trading strategy using LSTM deep learning model combined with
technical indicators and optional LLM analysis.

Strategy Components:
1. LSTM Price Prediction (40% weight): Neural network forecasting
2. Technical Analysis (40% weight): RSI, MACD, Bollinger Bands, Trend
3. LLM Strategy Analysis (20% weight): Natural language reasoning (optional)
4. Risk Assessment: Volatility analysis and position sizing

Entry Rules:
    LONG/STRONG_BUY:
        - AI ensemble confidence >= min_confidence
        - Final signal is BUY or STRONG_BUY
        - Risk-adjusted position sizing applied

    SHORT/STRONG_SELL:
        - AI ensemble confidence >= min_confidence
        - Final signal is SELL or STRONG_SELL
        - Risk-adjusted position sizing applied

Exit Rules:
    - Reverse signal from AI ensemble
    - ATR-based stop-loss/take-profit
    - Risk-based position management
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional
import logging
import asyncio

from .strategies import BaseStrategy, Signal
from .indicators import calculate_atr
from app.ai.signal_generator import SignalGenerator, SignalType

logger = logging.getLogger(__name__)


class LSTMStrategy(BaseStrategy):
    """
    LSTM AI Strategy

    Advanced AI-powered trading strategy combining deep learning price prediction,
    technical analysis, and optional LLM insights.

    Performance depends on:
        - Quality of trained LSTM model
        - Market conditions (works best in trending markets)
        - Risk management settings

    Args:
        min_confidence: Minimum confidence threshold (0-100) for trade entry
        lookback_hours: Number of hours for LSTM input sequence
        use_llm_analysis: Whether to include Llama 3.1 analysis (slower but more comprehensive)
        risk_per_trade: Risk percentage per trade for position sizing (default 2%)
        atr_sl_multiplier: ATR multiplier for stop-loss (default 1.5)
        atr_tp_multiplier: ATR multiplier for take-profit (default 3.0)
    """

    def __init__(
        self,
        min_confidence: float = 60.0,
        lookback_hours: int = 60,
        use_llm_analysis: bool = False,
        risk_per_trade: float = 2.0,
        atr_sl_multiplier: float = 1.5,
        atr_tp_multiplier: float = 3.0
    ):
        super().__init__("LSTM-AI")
        self.min_confidence = min_confidence
        self.lookback_hours = lookback_hours
        self.use_llm_analysis = use_llm_analysis
        self.risk_per_trade = risk_per_trade
        self.atr_sl_multiplier = atr_sl_multiplier
        self.atr_tp_multiplier = atr_tp_multiplier

        # Initialize signal generator
        self.signal_generator = SignalGenerator(min_confidence=min_confidence)

    def generate_signal(self, df: pd.DataFrame, current_price: float) -> Signal:
        """
        Generate AI-powered trading signal

        Args:
            df: DataFrame with OHLCV data and technical indicators
            current_price: Current market price

        Returns:
            Signal object with AI-based entry decision and risk-adjusted levels
        """

        try:
            # Extract symbol from dataframe (if available) or use default
            symbol = df.attrs.get('symbol', 'BTCUSDT')
            interval = df.attrs.get('interval', '1h')

            # Generate AI signal using async signal generator
            # Note: In backtesting, we run this synchronously
            ai_result = asyncio.run(
                self.signal_generator.generate_signal(
                    symbol=symbol,
                    interval=interval,
                    lookback_hours=self.lookback_hours,
                    use_llm_analysis=self.use_llm_analysis
                )
            )

            # Extract signal components
            signal_type = ai_result['signal']  # BUY, SELL, HOLD, STRONG_BUY, STRONG_SELL
            confidence = ai_result['confidence']  # 0-100
            recommendation = ai_result['recommendation']
            analysis = ai_result['analysis']

            # Convert AI signal to trading direction
            should_enter = False
            trade_direction = None

            if signal_type in [SignalType.BUY.value, SignalType.STRONG_BUY.value]:
                should_enter = True
                trade_direction = 'LONG'

            elif signal_type in [SignalType.SELL.value, SignalType.STRONG_SELL.value]:
                should_enter = True
                trade_direction = 'SHORT'

            # Calculate ATR for stop-loss/take-profit
            atr = calculate_atr(df, period=14)
            current_atr = atr.iloc[-1]

            # Calculate stop-loss and take-profit
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

            # Build comprehensive reasoning
            reasoning_parts = []

            # LSTM prediction
            lstm_info = analysis.get('lstm_prediction', {})
            if lstm_info:
                reasoning_parts.append(
                    f"LSTM: Predicted price ${lstm_info.get('predicted_price', 0):.2f} "
                    f"({lstm_info.get('change_pct', 0):+.2f}%)"
                )

            # Technical analysis
            technical_info = analysis.get('technical_analysis', {})
            if technical_info:
                tech_signals = []
                if technical_info.get('rsi'):
                    tech_signals.append(f"RSI={technical_info['rsi']['signal']}")
                if technical_info.get('macd'):
                    tech_signals.append(f"MACD={technical_info['macd']['signal']}")
                if technical_info.get('trend'):
                    tech_signals.append(f"Trend={technical_info['trend']['direction']}")

                if tech_signals:
                    reasoning_parts.append(f"Technical: {', '.join(tech_signals)}")

            # Risk assessment
            risk_info = analysis.get('risk_assessment', {})
            if risk_info:
                reasoning_parts.append(
                    f"Risk: Volatility={risk_info.get('volatility', 0):.2f}%, "
                    f"Position={recommendation.get('position_size_pct', 0):.1f}%"
                )

            reasoning = f"LSTM-AI {signal_type}: " + " | ".join(reasoning_parts)

            # Normalize confidence to 0.0-1.0 range
            normalized_confidence = confidence / 100.0

            return Signal(
                should_enter=should_enter,
                direction=trade_direction if should_enter else 'NEUTRAL',
                confidence=normalized_confidence,
                entry_price=current_price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                reasoning=reasoning,
                indicator_values={
                    'ai_signal': signal_type,
                    'ai_confidence': confidence,
                    'lstm_prediction': analysis.get('lstm_prediction', {}),
                    'technical_analysis': analysis.get('technical_analysis', {}),
                    'risk_assessment': analysis.get('risk_assessment', {}),
                    'position_size_pct': recommendation.get('position_size_pct', 0),
                    'atr': current_atr
                }
            )

        except FileNotFoundError as e:
            # LSTM model not found
            logger.error(f"LSTM model not found: {e}")
            return Signal(
                should_enter=False,
                direction='NEUTRAL',
                confidence=0.0,
                entry_price=current_price,
                reasoning=f"LSTM model not trained for {symbol}. Please train model first.",
                indicator_values={'error': str(e)}
            )

        except Exception as e:
            # Other errors
            logger.error(f"LSTM strategy error: {e}", exc_info=True)
            return Signal(
                should_enter=False,
                direction='NEUTRAL',
                confidence=0.0,
                entry_price=current_price,
                reasoning=f"Error generating signal: {str(e)}",
                indicator_values={'error': str(e)}
            )


class LSTMFastStrategy(LSTMStrategy):
    """
    Fast LSTM Strategy (No LLM Analysis)

    Optimized for speed by excluding Llama 3.1 LLM analysis.
    Response time: <3 seconds vs ~10 seconds for full strategy.

    Use Cases:
        - High-frequency backtesting
        - Real-time trading with low latency requirements
        - Initial strategy validation

    Trade-off:
        - Faster execution (~3x speed improvement)
        - Slightly lower accuracy (loses 20% LLM weight)
    """

    def __init__(
        self,
        min_confidence: float = 60.0,
        lookback_hours: int = 60,
        risk_per_trade: float = 2.0,
        atr_sl_multiplier: float = 1.5,
        atr_tp_multiplier: float = 3.0
    ):
        super().__init__(
            min_confidence=min_confidence,
            lookback_hours=lookback_hours,
            use_llm_analysis=False,  # Disable LLM for speed
            risk_per_trade=risk_per_trade,
            atr_sl_multiplier=atr_sl_multiplier,
            atr_tp_multiplier=atr_tp_multiplier
        )
        self.name = "LSTM-AI-Fast"


class LSTMConservativeStrategy(LSTMStrategy):
    """
    Conservative LSTM Strategy

    High-confidence trading with strict entry criteria.

    Features:
        - Higher confidence threshold (75% vs 60%)
        - LLM analysis enabled for additional validation
        - Lower risk per trade (1% vs 2%)
        - Wider stop-loss for lower false exits

    Use Cases:
        - Risk-averse traders
        - Volatile market conditions
        - Long-term position holding
    """

    def __init__(
        self,
        min_confidence: float = 75.0,
        lookback_hours: int = 60,
        risk_per_trade: float = 1.0,
        atr_sl_multiplier: float = 2.5,
        atr_tp_multiplier: float = 5.0
    ):
        super().__init__(
            min_confidence=min_confidence,
            lookback_hours=lookback_hours,
            use_llm_analysis=True,  # Enable LLM for extra validation
            risk_per_trade=risk_per_trade,
            atr_sl_multiplier=atr_sl_multiplier,
            atr_tp_multiplier=atr_tp_multiplier
        )
        self.name = "LSTM-AI-Conservative"


class LSTMAggressiveStrategy(LSTMStrategy):
    """
    Aggressive LSTM Strategy

    High-frequency trading with lower entry threshold.

    Features:
        - Lower confidence threshold (50% vs 60%)
        - No LLM analysis for speed
        - Higher risk per trade (5% vs 2%)
        - Tighter stop-loss for quick exits

    Use Cases:
        - Experienced traders
        - Trending markets
        - Short-term scalping

    ⚠️ WARNING: Higher risk, higher potential returns
    """

    def __init__(
        self,
        min_confidence: float = 50.0,
        lookback_hours: int = 60,
        risk_per_trade: float = 5.0,
        atr_sl_multiplier: float = 1.0,
        atr_tp_multiplier: float = 2.0
    ):
        super().__init__(
            min_confidence=min_confidence,
            lookback_hours=lookback_hours,
            use_llm_analysis=False,  # Disable LLM for speed
            risk_per_trade=risk_per_trade,
            atr_sl_multiplier=atr_sl_multiplier,
            atr_tp_multiplier=atr_tp_multiplier
        )
        self.name = "LSTM-AI-Aggressive"
