from typing import Dict, Tuple, Optional
from dataclasses import dataclass
import pandas as pd
import numpy as np
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


@dataclass
class SignalResult:
    """AI signal analysis result"""
    direction: str  # "LONG", "SHORT", or "NEUTRAL"
    probability: float  # 0.0 - 1.0
    confidence: float  # 0.0 - 1.0
    entry_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    reasoning: Optional[str] = None


@dataclass
class EnsembleDecision:
    """Final ensemble decision"""
    should_enter: bool
    direction: str  # "LONG" or "SHORT"
    probability_up: float  # Final probability
    confidence: float  # Overall confidence
    agreement: float  # Agreement level across AIs

    # Individual AI results
    ml_result: SignalResult
    gpt4_result: SignalResult
    llama_result: SignalResult
    ta_result: SignalResult

    # Trade parameters
    entry_price: float
    stop_loss: float
    take_profit: float
    reasoning: str


class TripleAIEnsemble:
    """
    Triple AI Ensemble System for trading signals

    Combines:
    - ML Models (40%): LSTM, Transformer, LightGBM
    - GPT-4 (25%): OpenAI analysis
    - LLaMA 3.1 (25%): Meta LLM analysis
    - Technical Analysis Rules (10%): ATR-based signals

    Entry Logic: Probability ≥80% AND Confidence ≥70% AND Agreement ≥70%
    """

    def __init__(self):
        self.ml_weight = settings.ML_WEIGHT
        self.gpt4_weight = settings.GPT4_WEIGHT
        self.llama_weight = settings.LLAMA_WEIGHT
        self.ta_weight = settings.TA_WEIGHT

        # Thresholds
        self.min_probability = settings.MIN_PROBABILITY
        self.min_confidence = settings.MIN_CONFIDENCE
        self.min_agreement = settings.MIN_AGREEMENT

        logger.info(f"Triple AI Ensemble initialized with weights: ML={self.ml_weight}, "
                   f"GPT4={self.gpt4_weight}, LLaMA={self.llama_weight}, TA={self.ta_weight}")

    async def analyze(
        self,
        symbol: str,
        market_data: pd.DataFrame,
        current_price: float
    ) -> EnsembleDecision:
        """
        Analyze market conditions using Triple AI Ensemble

        Args:
            symbol: Trading pair (e.g., "BTCUSDT")
            market_data: Historical OHLCV data
            current_price: Current market price

        Returns:
            EnsembleDecision with final trading signal
        """
        logger.info(f"Analyzing {symbol} with Triple AI Ensemble...")

        # 1. ML Models Analysis (40%)
        ml_result = await self._ml_analysis(market_data, current_price)

        # 2. GPT-4 Analysis (25%)
        gpt4_result = await self._gpt4_analysis(symbol, market_data, current_price)

        # 3. LLaMA 3.1 Analysis (25%)
        llama_result = await self._llama_analysis(symbol, market_data, current_price)

        # 4. Technical Analysis Rules (10%)
        ta_result = await self._ta_analysis(market_data, current_price)

        # 5. Calculate weighted ensemble
        probability_up = (
            self.ml_weight * ml_result.probability +
            self.gpt4_weight * gpt4_result.probability +
            self.llama_weight * llama_result.probability +
            self.ta_weight * ta_result.probability
        )

        # 6. Calculate overall confidence (average of all confidences)
        overall_confidence = np.mean([
            ml_result.confidence,
            gpt4_result.confidence,
            llama_result.confidence,
            ta_result.confidence
        ])

        # 7. Calculate agreement level
        directions = [
            ml_result.direction,
            gpt4_result.direction,
            llama_result.direction,
            ta_result.direction
        ]
        agreement = self._calculate_agreement(directions)

        # 8. Determine final direction
        final_direction = "LONG" if probability_up >= 0.5 else "SHORT"

        # 9. Entry decision logic
        should_enter = (
            probability_up >= self.min_probability and
            overall_confidence >= self.min_confidence and
            agreement >= self.min_agreement
        )

        # 10. Calculate trade parameters
        entry_price, stop_loss, take_profit = self._calculate_trade_params(
            market_data, current_price, final_direction
        )

        # 11. Generate reasoning
        reasoning = self._generate_reasoning(
            ml_result, gpt4_result, llama_result, ta_result,
            probability_up, overall_confidence, agreement
        )

        decision = EnsembleDecision(
            should_enter=should_enter,
            direction=final_direction,
            probability_up=probability_up,
            confidence=overall_confidence,
            agreement=agreement,
            ml_result=ml_result,
            gpt4_result=gpt4_result,
            llama_result=llama_result,
            ta_result=ta_result,
            entry_price=entry_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            reasoning=reasoning
        )

        logger.info(f"Ensemble Decision: {decision.direction} | "
                   f"Probability={decision.probability_up:.2%} | "
                   f"Confidence={decision.confidence:.2%} | "
                   f"Agreement={decision.agreement:.2%} | "
                   f"Enter={decision.should_enter}")

        return decision

    async def _ml_analysis(self, market_data: pd.DataFrame, current_price: float) -> SignalResult:
        """ML Models (LSTM + Transformer + LightGBM) analysis"""
        # TODO: Implement actual ML models
        # For now, return a mock result

        # Calculate basic technical indicators for demo
        close_prices = market_data['close'].values
        sma_20 = close_prices[-20:].mean()
        sma_50 = close_prices[-50:].mean()

        # Simple trend logic
        if sma_20 > sma_50:
            direction = "LONG"
            probability = 0.85
        else:
            direction = "SHORT"
            probability = 0.15

        return SignalResult(
            direction=direction,
            probability=probability,
            confidence=0.75,
            reasoning="ML Models: SMA20 > SMA50 indicates bullish trend"
        )

    async def _gpt4_analysis(
        self,
        symbol: str,
        market_data: pd.DataFrame,
        current_price: float
    ) -> SignalResult:
        """GPT-4 analysis via OpenAI API"""
        # TODO: Implement GPT-4 API call
        # For now, return a mock result

        return SignalResult(
            direction="LONG",
            probability=0.82,
            confidence=0.80,
            reasoning="GPT-4: Market structure shows bullish momentum with strong support levels"
        )

    async def _llama_analysis(
        self,
        symbol: str,
        market_data: pd.DataFrame,
        current_price: float
    ) -> SignalResult:
        """LLaMA 3.1 analysis via Anthropic API"""
        # TODO: Implement LLaMA API call
        # For now, return a mock result

        return SignalResult(
            direction="LONG",
            probability=0.78,
            confidence=0.72,
            reasoning="LLaMA: Volume profile suggests accumulation phase"
        )

    async def _ta_analysis(self, market_data: pd.DataFrame, current_price: float) -> SignalResult:
        """Technical Analysis Rules (ATR-based signals)"""
        from ta.volatility import AverageTrueRange
        from ta.trend import EMAIndicator

        # Calculate ATR
        atr = AverageTrueRange(
            high=market_data['high'],
            low=market_data['low'],
            close=market_data['close'],
            window=settings.ATR_PERIOD
        ).average_true_range()

        current_atr = atr.iloc[-1]

        # Calculate EMAs
        ema_20 = EMAIndicator(close=market_data['close'], window=20).ema_indicator()
        ema_50 = EMAIndicator(close=market_data['close'], window=50).ema_indicator()

        current_ema_20 = ema_20.iloc[-1]
        current_ema_50 = ema_50.iloc[-1]

        # Simple TA logic
        if current_price > current_ema_20 and current_ema_20 > current_ema_50:
            direction = "LONG"
            probability = 0.80
        elif current_price < current_ema_20 and current_ema_20 < current_ema_50:
            direction = "SHORT"
            probability = 0.20
        else:
            direction = "NEUTRAL"
            probability = 0.50

        return SignalResult(
            direction=direction,
            probability=probability,
            confidence=0.70,
            reasoning=f"TA: EMA20={current_ema_20:.2f}, EMA50={current_ema_50:.2f}, ATR={current_atr:.2f}"
        )

    def _calculate_agreement(self, directions: list[str]) -> float:
        """Calculate agreement level across all AI models"""
        # Count most common direction
        from collections import Counter
        direction_counts = Counter(directions)
        most_common_count = direction_counts.most_common(1)[0][1]

        # Agreement = (most common count) / (total count)
        agreement = most_common_count / len(directions)
        return agreement

    def _calculate_trade_params(
        self,
        market_data: pd.DataFrame,
        current_price: float,
        direction: str
    ) -> Tuple[float, float, float]:
        """Calculate entry, stop-loss, and take-profit prices"""
        from ta.volatility import AverageTrueRange

        # Calculate ATR for risk management
        atr = AverageTrueRange(
            high=market_data['high'],
            low=market_data['low'],
            close=market_data['close'],
            window=settings.ATR_PERIOD
        ).average_true_range()

        current_atr = atr.iloc[-1]

        # Entry at current price
        entry_price = current_price

        # Stop-loss and take-profit based on ATR multipliers
        if direction == "LONG":
            stop_loss = entry_price - (current_atr * settings.DEFAULT_LEVERAGE * 0.5)
            take_profit = entry_price + (current_atr * settings.DEFAULT_LEVERAGE * 1.0)
        else:  # SHORT
            stop_loss = entry_price + (current_atr * settings.DEFAULT_LEVERAGE * 0.5)
            take_profit = entry_price - (current_atr * settings.DEFAULT_LEVERAGE * 1.0)

        return entry_price, stop_loss, take_profit

    def _generate_reasoning(
        self,
        ml_result: SignalResult,
        gpt4_result: SignalResult,
        llama_result: SignalResult,
        ta_result: SignalResult,
        probability: float,
        confidence: float,
        agreement: float
    ) -> str:
        """Generate human-readable reasoning for the decision"""
        reasoning_parts = [
            f"🤖 ML Models ({self.ml_weight:.0%}): {ml_result.reasoning}",
            f"🧠 GPT-4 ({self.gpt4_weight:.0%}): {gpt4_result.reasoning}",
            f"🦙 LLaMA ({self.llama_weight:.0%}): {llama_result.reasoning}",
            f"📊 TA Rules ({self.ta_weight:.0%}): {ta_result.reasoning}",
            f"\n✅ Final: Probability={probability:.1%}, Confidence={confidence:.1%}, Agreement={agreement:.1%}"
        ]

        return "\n".join(reasoning_parts)
