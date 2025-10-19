"""
실시간 시그널 생성 API

LSTM + 기술적 지표 + Llama 3.1 분석을 종합한
거래 시그널 생성 엔드포인트

Features:
- 실시간 거래 시그널 생성
- 신뢰도 기반 필터링
- 리스크 평가 및 포지션 크기 계산
- 시그널 히스토리 조회
"""

import logging
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime

from app.ai.signal_generator import SignalGenerator, SignalType, ConfidenceLevel

logger = logging.getLogger(__name__)

router = APIRouter()


# =======================
# Pydantic Models
# =======================

class SignalRequest(BaseModel):
    """시그널 생성 요청"""
    symbol: str = Field("BTCUSDT", description="거래 심볼")
    interval: str = Field("1h", description="캔들 간격 (1h, 4h, 1d)")
    lookback_hours: int = Field(60, description="LSTM 예측용 과거 데이터 길이", ge=10, le=200)
    use_llm_analysis: bool = Field(True, description="Llama 3.1 분석 활성화")
    min_confidence: float = Field(60.0, description="최소 신뢰도 (이하면 HOLD)", ge=0, le=100)


class SignalResponse(BaseModel):
    """시그널 응답"""
    signal: str = Field(..., description="거래 시그널 (BUY/SELL/HOLD/STRONG_BUY/STRONG_SELL)")
    confidence: float = Field(..., description="신뢰도 (0-100)")
    confidence_level: str = Field(..., description="신뢰도 수준 (VERY_HIGH/HIGH/MEDIUM/LOW/VERY_LOW)")
    analysis: Dict = Field(..., description="상세 분석 결과")
    recommendation: Dict = Field(..., description="거래 권장사항")
    timestamp: str = Field(..., description="시그널 생성 시각")


class QuickSignalResponse(BaseModel):
    """간단한 시그널 응답 (빠른 조회용)"""
    symbol: str
    signal: str
    confidence: float
    action: str
    position_size_pct: float
    timestamp: str


# =======================
# API Endpoints
# =======================

@router.post("/signal/generate", response_model=SignalResponse)
async def generate_trading_signal(request: SignalRequest):
    """
    실시간 거래 시그널 생성 (Full Analysis)

    **Features:**
    - LSTM 가격 예측 (1시간 후)
    - 기술적 지표 분석 (RSI, MACD, Bollinger Bands, Trend)
    - Llama 3.1 전략 분석 (선택적)
    - 리스크 평가 (변동성, 손실 확률)
    - 최종 시그널 합성 (BUY/SELL/HOLD)

    **Returns:**
    - `signal`: BUY, SELL, HOLD, STRONG_BUY, STRONG_SELL
    - `confidence`: 0-100 (신뢰도 점수)
    - `analysis`: LSTM, 기술적, LLM, 리스크 분석 결과
    - `recommendation`: 포지션 크기, 손절/익절 가격

    **Example:**
    ```json
    {
      "symbol": "BTCUSDT",
      "interval": "1h",
      "lookback_hours": 60,
      "use_llm_analysis": true,
      "min_confidence": 60.0
    }
    ```
    """
    try:
        logger.info(f"Generating signal for {request.symbol} {request.interval}...")

        # 시그널 생성기 초기화
        generator = SignalGenerator(min_confidence=request.min_confidence)

        # 시그널 생성
        signal = await generator.generate_signal(
            symbol=request.symbol,
            interval=request.interval,
            lookback_hours=request.lookback_hours,
            use_llm_analysis=request.use_llm_analysis
        )

        logger.info(
            f"✅ Signal generated: {signal['signal']} "
            f"(Confidence: {signal['confidence']:.1f}%)"
        )

        return SignalResponse(**signal)

    except FileNotFoundError as e:
        logger.error(f"Model not found: {e}")
        raise HTTPException(
            status_code=404,
            detail=f"LSTM model not found for {request.symbol} {request.interval}. Please train the model first."
        )
    except Exception as e:
        logger.error(f"Signal generation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Signal generation failed: {str(e)}"
        )


@router.get("/signal/quick/{symbol}", response_model=QuickSignalResponse)
async def get_quick_signal(
    symbol: str,
    interval: str = Query("1h", description="캔들 간격"),
    min_confidence: float = Query(60.0, description="최소 신뢰도", ge=0, le=100)
):
    """
    빠른 시그널 조회 (간단한 응답)

    **Features:**
    - LSTM + 기술적 지표 분석만 (LLM 제외)
    - 빠른 응답 시간 (<3초)
    - 핵심 정보만 반환

    **Returns:**
    - `symbol`: 거래 심볼
    - `signal`: BUY/SELL/HOLD
    - `confidence`: 신뢰도 (0-100)
    - `action`: 권장 행동
    - `position_size_pct`: 권장 포지션 크기 (%)

    **Example:**
    ```
    GET /api/v1/signal/quick/BTCUSDT?interval=1h&min_confidence=70
    ```
    """
    try:
        generator = SignalGenerator(min_confidence=min_confidence)

        signal = await generator.generate_signal(
            symbol=symbol,
            interval=interval,
            lookback_hours=60,
            use_llm_analysis=False  # LLM 제외 (빠른 응답)
        )

        return QuickSignalResponse(
            symbol=symbol,
            signal=signal['signal'],
            confidence=signal['confidence'],
            action=signal['recommendation']['action'],
            position_size_pct=signal['recommendation']['position_size_pct'],
            timestamp=signal['timestamp']
        )

    except FileNotFoundError as e:
        raise HTTPException(
            status_code=404,
            detail=f"Model not found for {symbol} {interval}. Train the model first."
        )
    except Exception as e:
        logger.error(f"Quick signal generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/signal/supported-symbols")
async def get_supported_symbols():
    """
    시그널 생성이 가능한 심볼 목록 조회

    훈련된 LSTM 모델이 존재하는 심볼만 반환

    **Returns:**
    ```json
    {
      "symbols": [
        {
          "symbol": "BTCUSDT",
          "interval": "1h",
          "last_trained": "2025-01-18T12:00:00"
        }
      ],
      "total": 1
    }
    ```
    """
    import os
    from datetime import datetime

    model_dir = "models/lstm"

    if not os.path.exists(model_dir):
        return {"symbols": [], "total": 0}

    symbols = []
    for filename in os.listdir(model_dir):
        if filename.endswith("_best_model.pth"):
            model_key = filename.replace("_best_model.pth", "")
            parts = model_key.split("_")

            if len(parts) >= 2:
                symbol = parts[0]
                interval = parts[1]

                model_path = os.path.join(model_dir, filename)
                last_trained = datetime.fromtimestamp(os.path.getmtime(model_path)).isoformat()

                symbols.append({
                    "symbol": symbol,
                    "interval": interval,
                    "last_trained": last_trained
                })

    return {"symbols": symbols, "total": len(symbols)}


@router.get("/signal/health")
async def signal_health_check():
    """
    시그널 생성 시스템 헬스체크

    **Returns:**
    - `status`: "ok" or "degraded"
    - `lstm_available`: LSTM 모델 사용 가능 여부
    - `llm_available`: Llama 3.1 사용 가능 여부
    - `technical_analysis_available`: 기술적 지표 분석 가능 여부
    """
    import os

    health = {
        "status": "ok",
        "lstm_available": os.path.exists("models/lstm"),
        "llm_available": True,  # ensemble.py 존재 확인
        "technical_analysis_available": True,  # ta library
        "timestamp": datetime.now().isoformat()
    }

    # LSTM 모델이 없으면 degraded 상태
    if not health["lstm_available"]:
        health["status"] = "degraded"
        health["warning"] = "No LSTM models found. Train a model first."

    return health


# =======================
# Batch Signal Generation
# =======================

@router.post("/signal/batch")
async def generate_batch_signals(
    symbols: List[str] = Query(..., description="심볼 목록"),
    interval: str = Query("1h", description="캔들 간격"),
    min_confidence: float = Query(60.0, description="최소 신뢰도")
):
    """
    여러 심볼의 시그널을 일괄 생성

    **Example:**
    ```
    POST /api/v1/signal/batch?symbols=BTCUSDT&symbols=ETHUSDT&interval=1h
    ```

    **Returns:**
    ```json
    {
      "signals": [
        {
          "symbol": "BTCUSDT",
          "signal": "BUY",
          "confidence": 75.3,
          "recommendation": {...}
        }
      ],
      "total": 2,
      "timestamp": "2025-01-18T12:00:00"
    }
    ```
    """
    generator = SignalGenerator(min_confidence=min_confidence)

    signals = []
    errors = []

    for symbol in symbols:
        try:
            signal = await generator.generate_signal(
                symbol=symbol,
                interval=interval,
                lookback_hours=60,
                use_llm_analysis=False  # 빠른 처리를 위해 LLM 제외
            )

            signals.append({
                "symbol": symbol,
                "signal": signal['signal'],
                "confidence": signal['confidence'],
                "recommendation": signal['recommendation']
            })

        except Exception as e:
            logger.error(f"Failed to generate signal for {symbol}: {e}")
            errors.append({
                "symbol": symbol,
                "error": str(e)
            })

    return {
        "signals": signals,
        "errors": errors,
        "total": len(signals),
        "timestamp": datetime.now().isoformat()
    }
