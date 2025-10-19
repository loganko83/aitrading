"""
AI 가격 예측 API

LSTM 모델을 이용한 실시간 가격 예측 엔드포인트

Features:
- 실시간 가격 예측 (1시간 후)
- 모델 훈련 시작/상태 확인
- 성능 메트릭 조회
- 예측 신뢰도 평가
"""

import logging
import os
import asyncio
from datetime import datetime
from typing import Optional, Dict, List
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel, Field
import numpy as np
import torch

from app.ai.data_collector import MarketDataCollector
from app.ai.data_preprocessor import LSTMDataPreprocessor
from app.ai.lstm_model import create_model, PricePredictionLSTM
from app.ai.model_trainer import LSTMTrainer

logger = logging.getLogger(__name__)

router = APIRouter()


# =======================
# Pydantic Models
# =======================

class TrainingRequest(BaseModel):
    """모델 훈련 요청"""
    symbol: str = Field("BTCUSDT", description="거래 심볼")
    interval: str = Field("1h", description="캔들 간격 (1h, 4h, 1d)")
    days: int = Field(365, description="훈련 데이터 일수", ge=30, le=730)
    lookback_window: int = Field(60, description="과거 참조 길이", ge=10, le=200)
    epochs: int = Field(100, description="최대 에폭 수", ge=10, le=500)
    batch_size: int = Field(64, description="배치 크기", ge=16, le=256)
    learning_rate: float = Field(0.001, description="학습률", ge=0.0001, le=0.1)
    hidden_size: int = Field(128, description="LSTM 히든 크기", ge=32, le=512)
    num_layers: int = Field(3, description="LSTM 레이어 개수", ge=1, le=5)
    model_type: str = Field("standard", description="모델 타입 (standard, bidirectional, attention)")


class PredictionRequest(BaseModel):
    """가격 예측 요청"""
    symbol: str = Field("BTCUSDT", description="거래 심볼")
    interval: str = Field("1h", description="캔들 간격")
    lookback_hours: int = Field(60, description="과거 참조 시간", ge=10, le=200)


class PredictionResponse(BaseModel):
    """가격 예측 응답"""
    symbol: str = Field(..., description="거래 심볼")
    current_price: float = Field(..., description="현재 가격")
    predicted_price: float = Field(..., description="예측 가격 (1시간 후)")
    price_change_pct: float = Field(..., description="예상 변화율 (%)")
    direction: str = Field(..., description="방향 (UP, DOWN, NEUTRAL)")
    confidence: float = Field(..., description="신뢰도 (0-100)")
    prediction_time: str = Field(..., description="예측 시간")
    model_info: Dict = Field(..., description="모델 정보")


class ModelStatus(BaseModel):
    """모델 상태"""
    is_trained: bool = Field(..., description="훈련 완료 여부")
    model_exists: bool = Field(..., description="모델 파일 존재 여부")
    last_trained: Optional[str] = Field(None, description="마지막 훈련 시간")
    training_in_progress: bool = Field(False, description="훈련 진행 중")
    model_metrics: Optional[Dict] = Field(None, description="모델 성능 메트릭")


# =======================
# Global State
# =======================

# 모델 및 전처리기 캐시
_model_cache: Dict[str, PricePredictionLSTM] = {}
_preprocessor_cache: Dict[str, LSTMDataPreprocessor] = {}
_training_status: Dict[str, bool] = {}

MODEL_DIR = "models/lstm"
SCALER_DIR = "models/scalers"


# =======================
# Helper Functions
# =======================

def get_model_key(symbol: str, interval: str) -> str:
    """모델 캐시 키 생성"""
    return f"{symbol}_{interval}"


async def load_or_create_model(
    symbol: str,
    interval: str,
    input_size: int,
    model_type: str = "standard"
) -> PricePredictionLSTM:
    """
    모델 로드 또는 생성

    Args:
        symbol: 거래 심볼
        interval: 캔들 간격
        input_size: 입력 특징 개수
        model_type: 모델 타입

    Returns:
        LSTM 모델
    """
    model_key = get_model_key(symbol, interval)

    # 캐시 확인
    if model_key in _model_cache:
        logger.info(f"Using cached model for {model_key}")
        return _model_cache[model_key]

    # 모델 파일 확인
    model_path = os.path.join(MODEL_DIR, f"{model_key}_best_model.pth")

    if os.path.exists(model_path):
        # 기존 모델 로드
        logger.info(f"Loading existing model from {model_path}")

        model = create_model(
            input_size=input_size,
            model_type=model_type,
            hidden_size=128,
            num_layers=3,
            dropout=0.2
        )

        device = "cuda" if torch.cuda.is_available() else "cpu"
        trainer = LSTMTrainer(model, device=device)
        trainer.load_model(model_path)

        _model_cache[model_key] = trainer.model

        return trainer.model

    else:
        raise HTTPException(
            status_code=404,
            detail=f"Model not found for {symbol} {interval}. Please train the model first."
        )


async def load_preprocessor(symbol: str, interval: str) -> LSTMDataPreprocessor:
    """
    전처리기 로드

    Args:
        symbol: 거래 심볼
        interval: 캔들 간격

    Returns:
        전처리기
    """
    model_key = get_model_key(symbol, interval)

    # 캐시 확인
    if model_key in _preprocessor_cache:
        return _preprocessor_cache[model_key]

    # 스케일러 로드
    scaler_path = os.path.join(SCALER_DIR, model_key)

    if not os.path.exists(scaler_path):
        raise HTTPException(
            status_code=404,
            detail=f"Preprocessor not found for {symbol} {interval}. Please train the model first."
        )

    preprocessor = LSTMDataPreprocessor()
    preprocessor.load_scalers(scaler_path)

    _preprocessor_cache[model_key] = preprocessor

    return preprocessor


# =======================
# Background Training Task
# =======================

async def train_model_background(
    symbol: str,
    interval: str,
    days: int,
    lookback_window: int,
    epochs: int,
    batch_size: int,
    learning_rate: float,
    hidden_size: int,
    num_layers: int,
    model_type: str
):
    """
    백그라운드 모델 훈련 태스크

    Args:
        symbol: 거래 심볼
        interval: 캔들 간격
        days: 훈련 데이터 일수
        lookback_window: 과거 참조 길이
        epochs: 최대 에폭 수
        batch_size: 배치 크기
        learning_rate: 학습률
        hidden_size: LSTM 히든 크기
        num_layers: LSTM 레이어 개수
        model_type: 모델 타입
    """
    model_key = get_model_key(symbol, interval)

    try:
        logger.info(f"Starting background training for {model_key}...")

        # 1. 데이터 수집
        collector = MarketDataCollector()
        df = collector.prepare_dataset(symbol=symbol, interval=interval, days=days)

        # 2. 데이터 전처리
        preprocessor = LSTMDataPreprocessor(
            lookback_window=lookback_window,
            prediction_horizon=1,
            train_ratio=0.7,
            val_ratio=0.15
        )
        data = preprocessor.prepare_lstm_data(df)

        # 스케일러 저장
        scaler_dir = os.path.join(SCALER_DIR, model_key)
        preprocessor.save_scalers(scaler_dir)

        # 3. 모델 생성
        input_size = data['X_train'].shape[2]
        model = create_model(
            input_size=input_size,
            model_type=model_type,
            hidden_size=hidden_size,
            num_layers=num_layers,
            dropout=0.2
        )

        # 4. 훈련
        device = "cuda" if torch.cuda.is_available() else "cpu"
        trainer = LSTMTrainer(model, device=device, learning_rate=learning_rate)

        model_save_dir = os.path.join(MODEL_DIR, model_key)

        history = trainer.fit(
            X_train=data['X_train'],
            y_train=data['y_train'],
            X_val=data['X_val'],
            y_val=data['y_val'],
            epochs=epochs,
            batch_size=batch_size,
            early_stopping_patience=15,
            save_dir=model_save_dir
        )

        # 5. 평가
        metrics = trainer.evaluate(
            X_test=data['X_test'],
            y_test=data['y_test'],
            scaler=preprocessor
        )

        # 6. 최종 모델 저장
        final_model_path = os.path.join(MODEL_DIR, f"{model_key}_best_model.pth")
        trainer.save_model(MODEL_DIR, f"{model_key}_best_model.pth")

        # 캐시 업데이트
        _model_cache[model_key] = trainer.model
        _preprocessor_cache[model_key] = preprocessor

        logger.info(f"✅ Background training complete for {model_key}")
        logger.info(f"   RMSE: {metrics['rmse']:.2f}, MAE: {metrics['mae']:.2f}")

    except Exception as e:
        logger.error(f"Background training failed for {model_key}: {e}", exc_info=True)

    finally:
        _training_status[model_key] = False


# =======================
# API Endpoints
# =======================

@router.post("/ai/train", status_code=202)
async def start_training(
    request: TrainingRequest,
    background_tasks: BackgroundTasks
):
    """
    모델 훈련 시작 (백그라운드)

    Args:
        request: 훈련 요청 파라미터

    Returns:
        훈련 시작 확인 메시지
    """
    model_key = get_model_key(request.symbol, request.interval)

    # 이미 훈련 중인지 확인
    if _training_status.get(model_key, False):
        raise HTTPException(
            status_code=409,
            detail=f"Training already in progress for {request.symbol} {request.interval}"
        )

    # 훈련 상태 업데이트
    _training_status[model_key] = True

    # 백그라운드 태스크 추가
    background_tasks.add_task(
        train_model_background,
        symbol=request.symbol,
        interval=request.interval,
        days=request.days,
        lookback_window=request.lookback_window,
        epochs=request.epochs,
        batch_size=request.batch_size,
        learning_rate=request.learning_rate,
        hidden_size=request.hidden_size,
        num_layers=request.num_layers,
        model_type=request.model_type
    )

    logger.info(f"Training started for {model_key}")

    return {
        "success": True,
        "message": f"Training started for {request.symbol} {request.interval}",
        "model_key": model_key,
        "estimated_time_minutes": request.epochs * 0.5  # 대략적 추정
    }


@router.post("/ai/predict", response_model=PredictionResponse)
async def predict_price(request: PredictionRequest):
    """
    실시간 가격 예측

    Args:
        request: 예측 요청 파라미터

    Returns:
        가격 예측 결과
    """
    try:
        model_key = get_model_key(request.symbol, request.interval)

        # 1. 최신 데이터 수집
        collector = MarketDataCollector()
        df = collector.prepare_dataset(
            symbol=request.symbol,
            interval=request.interval,
            days=30  # 최근 30일 데이터
        )

        # 현재 가격
        current_price = df['close'].iloc[-1]

        # 2. 전처리기 로드
        preprocessor = await load_preprocessor(request.symbol, request.interval)

        # 3. 데이터 변환
        scaled_features, scaled_target = preprocessor.transform(df)

        # 최근 lookback_window 시간의 데이터
        X_recent = scaled_features[-request.lookback_hours:]
        X_recent = np.expand_dims(X_recent, axis=0)  # (1, lookback, features)

        # 4. 모델 로드
        input_size = X_recent.shape[2]
        model = await load_or_create_model(
            symbol=request.symbol,
            interval=request.interval,
            input_size=input_size
        )

        # 5. 예측
        model.eval()
        device = "cuda" if torch.cuda.is_available() else "cpu"
        X_tensor = torch.FloatTensor(X_recent).to(device)

        with torch.no_grad():
            prediction_scaled = model(X_tensor).cpu().numpy()

        # 6. 스케일 복원
        predicted_price = preprocessor.inverse_transform_target(prediction_scaled)[0][0]

        # 7. 결과 분석
        price_change_pct = ((predicted_price - current_price) / current_price) * 100

        if price_change_pct > 0.5:
            direction = "UP"
        elif price_change_pct < -0.5:
            direction = "DOWN"
        else:
            direction = "NEUTRAL"

        # 신뢰도 계산 (간단한 휴리스틱)
        confidence = min(100, abs(price_change_pct) * 10 + 50)

        return PredictionResponse(
            symbol=request.symbol,
            current_price=float(current_price),
            predicted_price=float(predicted_price),
            price_change_pct=float(price_change_pct),
            direction=direction,
            confidence=float(confidence),
            prediction_time=datetime.now().isoformat(),
            model_info={
                "model_type": "LSTM",
                "lookback_hours": request.lookback_hours,
                "interval": request.interval
            }
        )

    except Exception as e:
        logger.error(f"Prediction failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


@router.get("/ai/model-status", response_model=ModelStatus)
async def get_model_status(symbol: str = "BTCUSDT", interval: str = "1h"):
    """
    모델 상태 조회

    Args:
        symbol: 거래 심볼
        interval: 캔들 간격

    Returns:
        모델 상태 정보
    """
    model_key = get_model_key(symbol, interval)

    # 모델 파일 존재 확인
    model_path = os.path.join(MODEL_DIR, f"{model_key}_best_model.pth")
    model_exists = os.path.exists(model_path)

    # 훈련 진행 중 확인
    training_in_progress = _training_status.get(model_key, False)

    # 마지막 훈련 시간
    last_trained = None
    if model_exists:
        last_trained = datetime.fromtimestamp(os.path.getmtime(model_path)).isoformat()

    # 메트릭 로드 (있을 경우)
    metrics = None
    history_path = os.path.join(MODEL_DIR, model_key, "training_history.json")
    if os.path.exists(history_path):
        import json
        with open(history_path, 'r') as f:
            history = json.load(f)
            metrics = {
                "best_val_loss": history.get("best_val_loss"),
                "epochs_trained": history.get("epochs_trained")
            }

    return ModelStatus(
        is_trained=model_exists,
        model_exists=model_exists,
        last_trained=last_trained,
        training_in_progress=training_in_progress,
        model_metrics=metrics
    )


@router.get("/ai/supported-models")
async def get_supported_models():
    """
    훈련된 모델 목록 조회

    Returns:
        훈련된 모델 리스트
    """
    if not os.path.exists(MODEL_DIR):
        return {"models": []}

    models = []
    for filename in os.listdir(MODEL_DIR):
        if filename.endswith("_best_model.pth"):
            model_key = filename.replace("_best_model.pth", "")
            symbol, interval = model_key.split("_", 1)

            model_path = os.path.join(MODEL_DIR, filename)
            last_trained = datetime.fromtimestamp(os.path.getmtime(model_path)).isoformat()

            models.append({
                "symbol": symbol,
                "interval": interval,
                "last_trained": last_trained
            })

    return {"models": models, "total": len(models)}
