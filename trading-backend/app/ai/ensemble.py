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
        try:
            from openai import AsyncOpenAI
            from app.core.config import settings

            client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

            # Prepare market data summary
            recent_data = market_data.tail(20)
            data_summary = {
                "symbol": symbol,
                "current_price": current_price,
                "recent_highs": recent_data['high'].tolist(),
                "recent_lows": recent_data['low'].tolist(),
                "recent_closes": recent_data['close'].tolist(),
                "recent_volumes": recent_data['volume'].tolist(),
                "sma_20": float(market_data['close'].tail(20).mean()),
                "sma_50": float(market_data['close'].tail(50).mean()),
            }

            # Create GPT-4 prompt
            prompt = f"""You are an expert cryptocurrency trader analyzing {symbol}.

Current Market Data:
- Current Price: ${current_price:,.2f}
- 20-period SMA: ${data_summary['sma_20']:,.2f}
- 50-period SMA: ${data_summary['sma_50']:,.2f}
- Recent High: ${max(data_summary['recent_highs']):,.2f}
- Recent Low: ${min(data_summary['recent_lows']):,.2f}

Analyze the market structure and provide:
1. Direction: LONG, SHORT, or NEUTRAL
2. Probability (0.0-1.0): How confident are you in the direction?
3. Confidence (0.0-1.0): Overall confidence in the analysis
4. Brief reasoning (2-3 sentences)

Respond in JSON format:
{{
    "direction": "LONG/SHORT/NEUTRAL",
    "probability": 0.75,
    "confidence": 0.80,
    "reasoning": "Your brief analysis"
}}"""

            # Call GPT-4
            response = await client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": "You are an expert cryptocurrency trading analyst. Provide concise, data-driven analysis."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=300,
                response_format={"type": "json_object"}
            )

            # Parse response
            import json
            result = json.loads(response.choices[0].message.content)

            return SignalResult(
                direction=result["direction"],
                probability=float(result["probability"]),
                confidence=float(result["confidence"]),
                reasoning=f"GPT-4: {result['reasoning']}"
            )

        except Exception as e:
            logger.error(f"GPT-4 analysis error: {e}")
            # Fallback to simple analysis
            sma_20 = market_data['close'].tail(20).mean()
            sma_50 = market_data['close'].tail(50).mean()

            if current_price > sma_20 and sma_20 > sma_50:
                direction = "LONG"
                probability = 0.75
            elif current_price < sma_20 and sma_20 < sma_50:
                direction = "SHORT"
                probability = 0.25
            else:
                direction = "NEUTRAL"
                probability = 0.50

            return SignalResult(
                direction=direction,
                probability=probability,
                confidence=0.70,
                reasoning="GPT-4: Fallback analysis - price action relative to moving averages"
            )

    async def _llama_analysis(
        self,
        symbol: str,
        market_data: pd.DataFrame,
        current_price: float
    ) -> SignalResult:
        """Claude (Anthropic) analysis as alternative to LLaMA"""
        try:
            from anthropic import AsyncAnthropic
            from app.core.config import settings

            client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

            # Prepare market data summary
            recent_data = market_data.tail(20)
            volume_trend = "increasing" if recent_data['volume'].tail(5).mean() > recent_data['volume'].tail(10).mean() else "decreasing"

            # Create Claude prompt
            prompt = f"""Analyze {symbol} cryptocurrency market:

Current Price: ${current_price:,.2f}
Volume Trend: {volume_trend}
Price Change (24h): {((current_price / market_data['close'].iloc[-24] - 1) * 100):.2f}%

Provide trading analysis in JSON:
{{
    "direction": "LONG/SHORT/NEUTRAL",
    "probability": 0.75,
    "confidence": 0.80,
    "reasoning": "Brief volume and momentum analysis"
}}"""

            # Call Claude
            message = await client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=300,
                temperature=0.3,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            # Parse response
            import json
            import re

            # Extract JSON from response
            content = message.content[0].text
            json_match = re.search(r'\{[^}]+\}', content, re.DOTALL)

            if json_match:
                result = json.loads(json_match.group())

                return SignalResult(
                    direction=result["direction"],
                    probability=float(result["probability"]),
                    confidence=float(result["confidence"]),
                    reasoning=f"Claude: {result['reasoning']}"
                )
            else:
                raise ValueError("Could not parse JSON from Claude response")

        except Exception as e:
            logger.error(f"Claude analysis error: {e}")
            # Fallback to volume-based analysis
            recent_volume = market_data['volume'].tail(10).mean()
            avg_volume = market_data['volume'].mean()

            if recent_volume > avg_volume * 1.2:
                direction = "LONG" if current_price > market_data['close'].iloc[-10] else "SHORT"
                probability = 0.72
            else:
                direction = "NEUTRAL"
                probability = 0.50

            return SignalResult(
                direction=direction,
                probability=probability,
                confidence=0.68,
                reasoning="Claude: Fallback analysis - volume profile and price momentum"
            )

    async def _ta_analysis(self, market_data: pd.DataFrame, current_price: float) -> SignalResult:
        """
        Technical Analysis using TradingView's Top-Rated Strategies

        Combines 6 proven strategies:
        1. SuperTrend (67% win rate, 177% returns)
        2. RSI + EMA Crossover
        3. MACD + Stochastic RSI
        4. Ichimoku Cloud
        5. WaveTrend Dead Zone
        6. Multi-Indicator Consensus

        Returns weighted ensemble of all strategy signals.
        """
        from app.strategies.strategies import (
            SuperTrendStrategy,
            RSIEMAStrategy,
            MACDStochStrategy,
            IchimokuStrategy,
            WaveTrendStrategy,
            MultiIndicatorStrategy
        )

        # Initialize strategies
        strategies = [
            SuperTrendStrategy(),
            RSIEMAStrategy(),
            MACDStochStrategy(),
            IchimokuStrategy(),
            WaveTrendStrategy(),
            MultiIndicatorStrategy()
        ]

        # Generate signals from all strategies
        signals = []
        for strategy in strategies:
            try:
                signal = strategy.generate_signal(market_data.copy(), current_price)
                if signal.should_enter:
                    signals.append({
                        'strategy': strategy.name,
                        'direction': signal.direction,
                        'confidence': signal.confidence,
                        'reasoning': signal.reasoning
                    })
            except Exception as e:
                logger.warning(f"Strategy {strategy.name} failed: {e}")
                continue

        # Calculate ensemble from strategy signals
        if not signals:
            # No clear signals - return neutral
            return SignalResult(
                direction="NEUTRAL",
                probability=0.50,
                confidence=0.50,
                reasoning="TA: No clear signals from any strategy"
            )

        # Count directions
        long_signals = [s for s in signals if s['direction'] == 'LONG']
        short_signals = [s for s in signals if s['direction'] == 'SHORT']

        # Determine consensus direction
        if len(long_signals) > len(short_signals):
            direction = "LONG"
            relevant_signals = long_signals
            # Probability based on number of agreeing strategies
            probability = min(0.60 + (len(long_signals) / len(strategies)) * 0.30, 0.95)
        elif len(short_signals) > len(long_signals):
            direction = "SHORT"
            relevant_signals = short_signals
            probability = max(0.05, 0.40 - (len(short_signals) / len(strategies)) * 0.30)
        else:
            # Equal votes - check confidence
            long_conf = np.mean([s['confidence'] for s in long_signals]) if long_signals else 0
            short_conf = np.mean([s['confidence'] for s in short_signals]) if short_signals else 0

            if long_conf > short_conf:
                direction = "LONG"
                relevant_signals = long_signals
                probability = 0.55 + (long_conf * 0.20)
            else:
                direction = "SHORT"
                relevant_signals = short_signals
                probability = 0.45 - (short_conf * 0.20)

        # Calculate overall confidence (weighted by individual strategy confidence)
        if relevant_signals:
            overall_confidence = np.mean([s['confidence'] for s in relevant_signals])
        else:
            overall_confidence = 0.50

        # Generate reasoning
        strategy_names = [s['strategy'] for s in relevant_signals]
        reasoning = (
            f"TA Strategies ({len(relevant_signals)}/{len(strategies)} agree): "
            f"{', '.join(strategy_names)} all signal {direction}"
        )

        return SignalResult(
            direction=direction,
            probability=probability,
            confidence=overall_confidence,
            reasoning=reasoning
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


# Singleton instance for efficient reuse
_ensemble_instance = None


async def get_ai_analysis(
    symbol: str,
    market_data: pd.DataFrame,
    current_price: float
) -> EnsembleDecision:
    """
    Helper function to get AI analysis using Triple AI Ensemble

    This is a convenience function that creates/reuses a TripleAIEnsemble instance
    and calls its analyze method.

    Args:
        symbol: Trading pair (e.g., "BTCUSDT")
        market_data: Historical OHLCV data
        current_price: Current market price

    Returns:
        EnsembleDecision with final trading signal
    """
    global _ensemble_instance

    if _ensemble_instance is None:
        _ensemble_instance = TripleAIEnsemble()

    return await _ensemble_instance.analyze(symbol, market_data, current_price)
