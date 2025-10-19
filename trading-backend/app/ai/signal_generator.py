"""
실시간 시그널 생성 엔진

LSTM 가격 예측 + 기술적 지표 + Llama 3.1 전략 분석을 종합하여
최종 거래 시그널을 생성합니다.

Features:
- 다층 AI 분석 (LSTM + Technical + LLM)
- 리스크 평가 및 포지션 크기 계산
- 신뢰도 스코어 기반 필터링
- 실시간 시그널 생성
"""

import logging
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from enum import Enum

from app.ai.data_collector import MarketDataCollector
from app.ai.data_preprocessor import LSTMDataPreprocessor
from app.ai.lstm_model import PricePredictionLSTM
from app.ai.model_trainer import LSTMTrainer
from app.ai.ensemble import get_ai_analysis
import torch

logger = logging.getLogger(__name__)


# =======================
# Enums and Constants
# =======================

class SignalType(str, Enum):
    """시그널 타입"""
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"
    STRONG_BUY = "STRONG_BUY"
    STRONG_SELL = "STRONG_SELL"


class ConfidenceLevel(str, Enum):
    """신뢰도 수준"""
    VERY_HIGH = "VERY_HIGH"  # 90%+
    HIGH = "HIGH"            # 75-90%
    MEDIUM = "MEDIUM"        # 60-75%
    LOW = "LOW"              # 40-60%
    VERY_LOW = "VERY_LOW"    # <40%


# =======================
# Technical Indicator Analysis
# =======================

class TechnicalAnalyzer:
    """
    기술적 지표 분석기

    Features:
    - RSI, MACD, Bollinger Bands 분석
    - 트렌드 강도 계산
    - 과매수/과매도 감지
    """

    @staticmethod
    def analyze_rsi(df: pd.DataFrame) -> Dict:
        """
        RSI 분석

        Returns:
            {
                'value': RSI 값,
                'signal': 'oversold' | 'overbought' | 'neutral',
                'strength': 0-100 (신호 강도)
            }
        """
        rsi = df['rsi'].iloc[-1]

        if rsi < 30:
            signal = "oversold"
            strength = (30 - rsi) / 30 * 100  # 더 낮을수록 강함
        elif rsi > 70:
            signal = "overbought"
            strength = (rsi - 70) / 30 * 100  # 더 높을수록 강함
        else:
            signal = "neutral"
            strength = 0

        return {
            "value": float(rsi),
            "signal": signal,
            "strength": float(min(100, strength))
        }

    @staticmethod
    def analyze_macd(df: pd.DataFrame) -> Dict:
        """
        MACD 분석

        Returns:
            {
                'macd': MACD 값,
                'signal': Signal 라인,
                'histogram': 히스토그램,
                'trend': 'bullish' | 'bearish' | 'neutral',
                'strength': 0-100
            }
        """
        macd = df['macd'].iloc[-1]
        signal = df['macd_signal'].iloc[-1]
        histogram = df['macd_diff'].iloc[-1]

        # 추세 판단
        if histogram > 0 and macd > signal:
            trend = "bullish"
            strength = min(100, abs(histogram) * 100)
        elif histogram < 0 and macd < signal:
            trend = "bearish"
            strength = min(100, abs(histogram) * 100)
        else:
            trend = "neutral"
            strength = 0

        return {
            "macd": float(macd),
            "signal": float(signal),
            "histogram": float(histogram),
            "trend": trend,
            "strength": float(strength)
        }

    @staticmethod
    def analyze_bollinger_bands(df: pd.DataFrame) -> Dict:
        """
        볼린저 밴드 분석

        Returns:
            {
                'position': 'upper' | 'lower' | 'middle',
                'width': 밴드 폭 (변동성),
                'signal': 'breakout_up' | 'breakout_down' | 'neutral',
                'strength': 0-100
            }
        """
        close = df['close'].iloc[-1]
        bb_high = df['bb_high'].iloc[-1]
        bb_mid = df['bb_mid'].iloc[-1]
        bb_low = df['bb_low'].iloc[-1]
        bb_width = df['bb_width'].iloc[-1]

        # 위치 판단
        if close > bb_high:
            position = "upper"
            signal = "breakout_up"
            strength = (close - bb_high) / (bb_high - bb_mid) * 100
        elif close < bb_low:
            position = "lower"
            signal = "breakout_down"
            strength = (bb_low - close) / (bb_mid - bb_low) * 100
        else:
            position = "middle"
            signal = "neutral"
            strength = 0

        return {
            "position": position,
            "width": float(bb_width),
            "signal": signal,
            "strength": float(min(100, strength))
        }

    @staticmethod
    def analyze_trend(df: pd.DataFrame) -> Dict:
        """
        EMA 기반 트렌드 분석

        Returns:
            {
                'trend': 'strong_uptrend' | 'uptrend' | 'downtrend' | 'strong_downtrend' | 'sideways',
                'strength': 0-100,
                'ema_alignment': EMA 정렬 상태
            }
        """
        close = df['close'].iloc[-1]
        ema_9 = df['ema_9'].iloc[-1]
        ema_21 = df['ema_21'].iloc[-1]
        ema_50 = df['ema_50'].iloc[-1]

        # EMA 정렬 확인
        if ema_9 > ema_21 > ema_50 > close:
            trend = "strong_uptrend"
            strength = 100
            ema_alignment = "perfect_bullish"
        elif ema_9 > ema_21 > ema_50:
            trend = "uptrend"
            strength = 75
            ema_alignment = "bullish"
        elif ema_9 < ema_21 < ema_50 < close:
            trend = "strong_downtrend"
            strength = 100
            ema_alignment = "perfect_bearish"
        elif ema_9 < ema_21 < ema_50:
            trend = "downtrend"
            strength = 75
            ema_alignment = "bearish"
        else:
            trend = "sideways"
            strength = 30
            ema_alignment = "mixed"

        return {
            "trend": trend,
            "strength": float(strength),
            "ema_alignment": ema_alignment
        }


# =======================
# Risk Assessment
# =======================

class RiskAssessor:
    """
    리스크 평가 모듈

    Features:
    - 변동성 분석
    - 손실 확률 계산
    - 최대 드로우다운 추정
    - 포지션 크기 계산
    """

    @staticmethod
    def calculate_volatility(df: pd.DataFrame, window: int = 20) -> float:
        """
        변동성 계산 (ATR 기반)

        Returns:
            변동성 비율 (0-100)
        """
        atr = df['atr'].iloc[-1]
        close = df['close'].iloc[-1]

        volatility_ratio = (atr / close) * 100

        return float(volatility_ratio)

    @staticmethod
    def estimate_loss_probability(
        predicted_change: float,
        confidence: float,
        volatility: float
    ) -> float:
        """
        손실 확률 추정

        Args:
            predicted_change: 예측된 가격 변화율 (%)
            confidence: 예측 신뢰도 (0-100)
            volatility: 변동성 비율 (0-100)

        Returns:
            손실 확률 (0-100)
        """
        # 기본 손실 확률
        base_loss_prob = 50

        # 예측 방향에 따른 조정
        if predicted_change > 0:
            direction_adjustment = -predicted_change * 2
        else:
            direction_adjustment = abs(predicted_change) * 2

        # 신뢰도에 따른 조정
        confidence_adjustment = -(confidence - 50) / 2

        # 변동성에 따른 조정
        volatility_adjustment = volatility * 0.5

        # 최종 확률 계산
        loss_prob = base_loss_prob + direction_adjustment + confidence_adjustment + volatility_adjustment

        return float(np.clip(loss_prob, 0, 100))

    @staticmethod
    def calculate_position_size(
        confidence: float,
        volatility: float,
        risk_per_trade: float = 2.0
    ) -> float:
        """
        포지션 크기 계산

        Args:
            confidence: 신뢰도 (0-100)
            volatility: 변동성 비율 (0-100)
            risk_per_trade: 거래당 최대 리스크 (% of capital)

        Returns:
            권장 포지션 크기 (% of capital)
        """
        # 기본 포지션 크기
        base_size = risk_per_trade

        # 신뢰도 기반 조정
        confidence_multiplier = confidence / 100

        # 변동성 기반 조정 (변동성 높으면 줄임)
        volatility_divisor = max(1, volatility / 10)

        # 최종 포지션 크기
        position_size = (base_size * confidence_multiplier) / volatility_divisor

        # 상한/하한 제한
        position_size = np.clip(position_size, 0.5, 10.0)

        return float(position_size)


# =======================
# Main Signal Generator
# =======================

class SignalGenerator:
    """
    실시간 시그널 생성 엔진

    Features:
    - LSTM 가격 예측
    - 기술적 지표 분석
    - Llama 3.1 전략 분석
    - 리스크 평가
    - 최종 시그널 생성
    """

    def __init__(
        self,
        model_dir: str = "models/lstm",
        scaler_dir: str = "models/scalers",
        min_confidence: float = 60.0
    ):
        """
        Args:
            model_dir: LSTM 모델 저장 디렉토리
            scaler_dir: 스케일러 저장 디렉토리
            min_confidence: 최소 신뢰도 (이하면 HOLD)
        """
        self.model_dir = model_dir
        self.scaler_dir = scaler_dir
        self.min_confidence = min_confidence

        self.technical_analyzer = TechnicalAnalyzer()
        self.risk_assessor = RiskAssessor()

    async def generate_signal(
        self,
        symbol: str = "BTCUSDT",
        interval: str = "1h",
        lookback_hours: int = 60,
        use_llm_analysis: bool = True
    ) -> Dict:
        """
        실시간 거래 시그널 생성

        Args:
            symbol: 거래 심볼
            interval: 캔들 간격
            lookback_hours: LSTM 예측용 과거 데이터 길이
            use_llm_analysis: Llama 3.1 분석 활성화 여부

        Returns:
            {
                'signal': SignalType,
                'confidence': 0-100,
                'confidence_level': ConfidenceLevel,
                'analysis': {
                    'lstm_prediction': {...},
                    'technical_analysis': {...},
                    'llm_analysis': {...} (optional),
                    'risk_assessment': {...}
                },
                'recommendation': {
                    'action': str,
                    'position_size': float,
                    'stop_loss': float,
                    'take_profit': float
                },
                'timestamp': ISO 8601 timestamp
            }
        """
        logger.info(f"Generating signal for {symbol} {interval}...")

        # 1. 데이터 수집
        collector = MarketDataCollector()
        df = collector.prepare_dataset(symbol=symbol, interval=interval, days=30)

        current_price = df['close'].iloc[-1]

        # 2. LSTM 가격 예측
        lstm_result = await self._get_lstm_prediction(
            symbol, interval, df, lookback_hours
        )

        # 3. 기술적 지표 분석
        technical_result = self._analyze_technical_indicators(df)

        # 4. Llama 3.1 전략 분석 (선택적)
        llm_result = None
        if use_llm_analysis:
            llm_result = await self._get_llm_analysis(symbol, df, lstm_result, technical_result)

        # 5. 리스크 평가
        risk_result = self._assess_risk(
            df, lstm_result, technical_result
        )

        # 6. 최종 시그널 합성
        final_signal = self._synthesize_signal(
            current_price,
            lstm_result,
            technical_result,
            llm_result,
            risk_result
        )

        logger.info(
            f"✅ Signal generated: {final_signal['signal']} "
            f"(Confidence: {final_signal['confidence']:.1f}%)"
        )

        return final_signal

    async def _get_lstm_prediction(
        self,
        symbol: str,
        interval: str,
        df: pd.DataFrame,
        lookback_hours: int
    ) -> Dict:
        """LSTM 가격 예측"""
        try:
            # 전처리기 로드
            model_key = f"{symbol}_{interval}"
            scaler_path = f"{self.scaler_dir}/{model_key}"

            preprocessor = LSTMDataPreprocessor()
            preprocessor.load_scalers(scaler_path)

            # 데이터 변환
            scaled_features, _ = preprocessor.transform(df)

            # 시퀀스 생성
            X_recent = scaled_features[-lookback_hours:]
            X_recent = np.expand_dims(X_recent, axis=0)

            # 모델 로드 및 예측
            model_path = f"{self.model_dir}/{model_key}_best_model.pth"

            input_size = X_recent.shape[2]
            model = PricePredictionLSTM(input_size=input_size)

            device = "cuda" if torch.cuda.is_available() else "cpu"
            trainer = LSTMTrainer(model, device=device)
            trainer.load_model(model_path)

            model.eval()
            X_tensor = torch.FloatTensor(X_recent).to(device)

            with torch.no_grad():
                prediction_scaled = model(X_tensor).cpu().numpy()

            # 스케일 복원
            predicted_price = preprocessor.inverse_transform_target(prediction_scaled)[0][0]

            current_price = df['close'].iloc[-1]
            price_change_pct = ((predicted_price - current_price) / current_price) * 100

            # 신뢰도 계산 (간단한 휴리스틱)
            confidence = min(100, abs(price_change_pct) * 10 + 50)

            return {
                "current_price": float(current_price),
                "predicted_price": float(predicted_price),
                "price_change_pct": float(price_change_pct),
                "confidence": float(confidence),
                "direction": "UP" if price_change_pct > 0 else "DOWN"
            }

        except Exception as e:
            logger.error(f"LSTM prediction failed: {e}")
            return {
                "error": str(e),
                "confidence": 0
            }

    def _analyze_technical_indicators(self, df: pd.DataFrame) -> Dict:
        """기술적 지표 분석"""
        rsi_analysis = self.technical_analyzer.analyze_rsi(df)
        macd_analysis = self.technical_analyzer.analyze_macd(df)
        bb_analysis = self.technical_analyzer.analyze_bollinger_bands(df)
        trend_analysis = self.technical_analyzer.analyze_trend(df)

        # 종합 기술적 점수 계산
        technical_score = (
            rsi_analysis['strength'] * 0.25 +
            macd_analysis['strength'] * 0.30 +
            bb_analysis['strength'] * 0.20 +
            trend_analysis['strength'] * 0.25
        )

        # 방향 판단
        bullish_signals = 0
        bearish_signals = 0

        if rsi_analysis['signal'] == 'oversold':
            bullish_signals += 1
        elif rsi_analysis['signal'] == 'overbought':
            bearish_signals += 1

        if macd_analysis['trend'] == 'bullish':
            bullish_signals += 1
        elif macd_analysis['trend'] == 'bearish':
            bearish_signals += 1

        if bb_analysis['signal'] == 'breakout_up':
            bullish_signals += 1
        elif bb_analysis['signal'] == 'breakout_down':
            bearish_signals += 1

        if 'uptrend' in trend_analysis['trend']:
            bullish_signals += 1
        elif 'downtrend' in trend_analysis['trend']:
            bearish_signals += 1

        overall_direction = "BULLISH" if bullish_signals > bearish_signals else "BEARISH" if bearish_signals > bullish_signals else "NEUTRAL"

        return {
            "rsi": rsi_analysis,
            "macd": macd_analysis,
            "bollinger_bands": bb_analysis,
            "trend": trend_analysis,
            "technical_score": float(technical_score),
            "overall_direction": overall_direction,
            "bullish_signals": bullish_signals,
            "bearish_signals": bearish_signals
        }

    async def _get_llm_analysis(
        self,
        symbol: str,
        df: pd.DataFrame,
        lstm_result: Dict,
        technical_result: Dict
    ) -> Optional[Dict]:
        """Llama 3.1 전략 분석"""
        try:
            # ensemble.py의 get_ai_analysis 활용
            strategy_name = "AI Signal Generator"
            params = {
                "symbol": symbol,
                "lstm_prediction": lstm_result,
                "technical_analysis": technical_result
            }

            # Historical data for context
            recent_data = df.tail(24).to_dict('records')

            # AI 분석 요청
            analysis = await get_ai_analysis(
                strategy_name=strategy_name,
                params=params,
                historical_data=recent_data
            )

            return {
                "analysis": analysis.get('analysis', ''),
                "recommendation": analysis.get('recommendations', []),
                "confidence": analysis.get('confidence', 0)
            }

        except Exception as e:
            logger.warning(f"LLM analysis failed: {e}")
            return None

    def _assess_risk(
        self,
        df: pd.DataFrame,
        lstm_result: Dict,
        technical_result: Dict
    ) -> Dict:
        """리스크 평가"""
        # 변동성 계산
        volatility = self.risk_assessor.calculate_volatility(df)

        # 손실 확률 추정
        predicted_change = lstm_result.get('price_change_pct', 0)
        confidence = lstm_result.get('confidence', 50)

        loss_probability = self.risk_assessor.estimate_loss_probability(
            predicted_change, confidence, volatility
        )

        # 포지션 크기 계산
        position_size = self.risk_assessor.calculate_position_size(
            confidence, volatility
        )

        # ATR 기반 손절/익절 계산
        atr = df['atr'].iloc[-1]
        current_price = df['close'].iloc[-1]

        stop_loss_distance = atr * 2  # ATR의 2배
        take_profit_distance = atr * 3  # ATR의 3배 (Risk:Reward = 1:1.5)

        return {
            "volatility": float(volatility),
            "loss_probability": float(loss_probability),
            "position_size_pct": float(position_size),
            "stop_loss_distance": float(stop_loss_distance),
            "take_profit_distance": float(take_profit_distance),
            "risk_reward_ratio": 1.5
        }

    def _synthesize_signal(
        self,
        current_price: float,
        lstm_result: Dict,
        technical_result: Dict,
        llm_result: Optional[Dict],
        risk_result: Dict
    ) -> Dict:
        """최종 시그널 합성"""

        # 1. 각 분석의 가중 점수 계산
        lstm_score = lstm_result.get('confidence', 0) * 0.40  # LSTM 40%
        technical_score = technical_result.get('technical_score', 0) * 0.40  # Technical 40%
        llm_score = (llm_result.get('confidence', 0) if llm_result else 50) * 0.20  # LLM 20%

        # 2. 최종 신뢰도
        final_confidence = lstm_score + technical_score + llm_score

        # 3. 신뢰도 수준 분류
        if final_confidence >= 90:
            confidence_level = ConfidenceLevel.VERY_HIGH
        elif final_confidence >= 75:
            confidence_level = ConfidenceLevel.HIGH
        elif final_confidence >= 60:
            confidence_level = ConfidenceLevel.MEDIUM
        elif final_confidence >= 40:
            confidence_level = ConfidenceLevel.LOW
        else:
            confidence_level = ConfidenceLevel.VERY_LOW

        # 4. 방향 판단
        lstm_direction = lstm_result.get('direction', 'NEUTRAL')
        technical_direction = technical_result.get('overall_direction', 'NEUTRAL')

        bullish_votes = 0
        bearish_votes = 0

        if lstm_direction == 'UP':
            bullish_votes += 1
        elif lstm_direction == 'DOWN':
            bearish_votes += 1

        if technical_direction == 'BULLISH':
            bullish_votes += 1
        elif technical_direction == 'BEARISH':
            bearish_votes += 1

        # 5. 최종 시그널 결정
        if final_confidence < self.min_confidence:
            signal = SignalType.HOLD
        elif bullish_votes > bearish_votes:
            signal = SignalType.STRONG_BUY if final_confidence >= 85 else SignalType.BUY
        elif bearish_votes > bullish_votes:
            signal = SignalType.STRONG_SELL if final_confidence >= 85 else SignalType.SELL
        else:
            signal = SignalType.HOLD

        # 6. 손절/익절 가격 계산
        if signal in [SignalType.BUY, SignalType.STRONG_BUY]:
            stop_loss = current_price - risk_result['stop_loss_distance']
            take_profit = current_price + risk_result['take_profit_distance']
        elif signal in [SignalType.SELL, SignalType.STRONG_SELL]:
            stop_loss = current_price + risk_result['stop_loss_distance']
            take_profit = current_price - risk_result['take_profit_distance']
        else:
            stop_loss = None
            take_profit = None

        # 7. 최종 결과 반환
        return {
            "signal": signal.value,
            "confidence": float(final_confidence),
            "confidence_level": confidence_level.value,
            "analysis": {
                "lstm_prediction": lstm_result,
                "technical_analysis": technical_result,
                "llm_analysis": llm_result,
                "risk_assessment": risk_result
            },
            "recommendation": {
                "action": signal.value,
                "position_size_pct": float(risk_result['position_size_pct']),
                "stop_loss": float(stop_loss) if stop_loss else None,
                "take_profit": float(take_profit) if take_profit else None,
                "risk_reward_ratio": float(risk_result['risk_reward_ratio'])
            },
            "timestamp": datetime.now().isoformat()
        }


# =======================
# 사용 예시
# =======================

if __name__ == "__main__":
    import asyncio

    # 로깅 설정
    logging.basicConfig(level=logging.INFO)

    async def test_signal_generator():
        """시그널 생성기 테스트"""
        generator = SignalGenerator(min_confidence=60.0)

        # BTCUSDT 시그널 생성
        signal = await generator.generate_signal(
            symbol="BTCUSDT",
            interval="1h",
            lookback_hours=60,
            use_llm_analysis=True
        )

        print("\n=== 거래 시그널 ===")
        print(f"시그널: {signal['signal']}")
        print(f"신뢰도: {signal['confidence']:.1f}% ({signal['confidence_level']})")
        print(f"\nLSTM 예측: {signal['analysis']['lstm_prediction']['price_change_pct']:.2f}%")
        print(f"기술적 분석: {signal['analysis']['technical_analysis']['overall_direction']}")
        print(f"\n권장사항:")
        print(f"  포지션 크기: {signal['recommendation']['position_size_pct']:.2f}%")
        print(f"  손절가: ${signal['recommendation']['stop_loss']:.2f}")
        print(f"  익절가: ${signal['recommendation']['take_profit']:.2f}")

    # 실행
    asyncio.run(test_signal_generator())
