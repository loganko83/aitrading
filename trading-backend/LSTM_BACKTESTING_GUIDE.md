# LSTM AI 백테스팅 가이드

**Phase 6 완료**: LSTM 딥러닝 전략이 백테스팅 시스템에 성공적으로 통합되었습니다.

---

## 📋 목차

1. [시스템 개요](#시스템-개요)
2. [사전 요구사항](#사전-요구사항)
3. [LSTM 모델 훈련](#lstm-모델-훈련)
4. [백테스팅 실행](#백테스팅-실행)
5. [전략 비교](#전략-비교)
6. [성능 최적화](#성능-최적화)

---

## 시스템 개요

### LSTM AI 전략 아키텍처

```
1. 데이터 수집 (MarketDataCollector)
   ↓ Binance API → OHLCV + 15개 기술적 지표

2. LSTM 가격 예측 (40% 가중치)
   ↓ PyTorch LSTM 모델 → 1시간 후 가격 예측

3. 기술적 분석 (40% 가중치)
   ↓ RSI, MACD, Bollinger Bands, Trend

4. LLM 전략 분석 (20% 가중치, 선택적)
   ↓ Llama 3.1 → 자연어 전략 분석

5. 리스크 평가
   ↓ 변동성, 손실 확률, 포지션 크기 계산

6. 최종 시그널 생성
   ↓ BUY / SELL / HOLD / STRONG_BUY / STRONG_SELL

7. 백테스팅 실행 (BacktestEngine)
   ↓ 실제 거래 시뮬레이션 (수수료, 레버리지, SL/TP)

8. 성과 분석
   → 승률, 수익률, Sharpe Ratio, MDD 등
```

### 전략 종류

| 전략 ID | 전략명 | 신뢰도 임계값 | LLM 분석 | 리스크/거래 | 속도 | 적합한 사용자 |
|--------|--------|---------------|----------|-------------|------|---------------|
| `lstm` | Full | 60% | ✅ | 2% | 보통 (~10초) | 균형잡힌 트레이더 |
| `lstm_fast` | Fast | 60% | ❌ | 2% | 빠름 (~3초) | 고빈도 백테스팅 |
| `lstm_conservative` | Conservative | 75% | ✅ | 1% | 느림 (~12초) | 보수적 트레이더 |
| `lstm_aggressive` | Aggressive | 50% | ❌ | 5% | 빠름 (~3초) | 공격적 트레이더 ⚠️ |

---

## 사전 요구사항

### 1. Python 패키지 설치

```bash
pip install torch pandas numpy scikit-learn ta asyncio
```

### 2. LSTM 모델 훈련 (필수)

LSTM 백테스팅을 실행하기 전에 **반드시 모델을 훈련**해야 합니다.

```bash
# 서버 실행
cd C:\dev\trading\trading-backend
python main.py
```

---

## LSTM 모델 훈련

### API 엔드포인트: `POST /api/v1/ai/train`

**Request:**
```json
{
  "symbol": "BTCUSDT",
  "interval": "1h",
  "days": 365,
  "lookback_window": 60,
  "epochs": 100,
  "batch_size": 64,
  "learning_rate": 0.001,
  "hidden_size": 128,
  "num_layers": 3,
  "model_type": "standard"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Training started for BTCUSDT 1h",
  "model_key": "BTCUSDT_1h",
  "estimated_time_minutes": 50
}
```

### cURL 예시

```bash
curl -X POST "http://localhost:8001/api/v1/ai/train" \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "BTCUSDT",
    "interval": "1h",
    "days": 365,
    "epochs": 100
  }'
```

### 훈련 진행 상태 확인

```bash
curl "http://localhost:8001/api/v1/ai/model-status?symbol=BTCUSDT&interval=1h"
```

**Response:**
```json
{
  "is_trained": true,
  "model_exists": true,
  "last_trained": "2025-01-18T15:30:00",
  "training_in_progress": false,
  "model_metrics": {
    "best_val_loss": 0.0012,
    "epochs_trained": 45
  }
}
```

### 모델 파일 위치

```
trading-backend/
├─ models/
│  ├─ lstm/
│  │  ├─ BTCUSDT_1h_best_model.pth  ← PyTorch 모델
│  │  └─ BTCUSDT_1h/
│  │     └─ training_history.json
│  └─ scalers/
│     └─ BTCUSDT_1h/
│        ├─ feature_scaler.pkl
│        └─ target_scaler.pkl
```

---

## 백테스팅 실행

### 1. LSTM 전략 백테스트 (Full)

**API 엔드포인트**: `POST /api/v1/backtest/run`

```json
{
  "strategy_type": "lstm",
  "symbol": "BTCUSDT",
  "initial_capital": 10000.0,
  "leverage": 3,
  "position_size_pct": 0.10,
  "days_back": 30,
  "maker_fee": 0.0002,
  "taker_fee": 0.0004,
  "custom_params": {
    "min_confidence": 60.0,
    "lookback_hours": 60,
    "use_llm_analysis": true,
    "risk_per_trade": 2.0
  }
}
```

**Response (간략):**
```json
{
  "strategy_name": "LSTM-AI",
  "symbol": "BTCUSDT",
  "start_date": "2025-01-01T00:00:00",
  "end_date": "2025-01-30T23:00:00",

  "total_trades": 15,
  "winning_trades": 10,
  "losing_trades": 5,
  "win_rate": 66.67,

  "total_return": 1500.0,
  "total_return_pct": 15.0,
  "annualized_return": 182.5,

  "max_drawdown": 500.0,
  "max_drawdown_pct": 5.0,

  "sharpe_ratio": 2.3,
  "sortino_ratio": 3.1,
  "profit_factor": 2.5,

  "avg_win": 200.0,
  "avg_loss": -80.0,
  "performance_rating": "EXCELLENT",

  "trades": [...],
  "equity_curve": [...],
  "drawdown_curve": [...]
}
```

### 2. LSTM Fast 백테스트 (빠른 검증)

```json
{
  "strategy_type": "lstm_fast",
  "symbol": "BTCUSDT",
  "initial_capital": 10000.0,
  "days_back": 30
}
```

**특징**: LLM 분석 제외로 **3배 빠른 실행** (~3초 vs ~10초)

### 3. LSTM Conservative 백테스트 (보수적)

```json
{
  "strategy_type": "lstm_conservative",
  "symbol": "BTCUSDT",
  "initial_capital": 10000.0,
  "days_back": 30
}
```

**특징**:
- 신뢰도 75% 이상에서만 진입
- 리스크 1%/거래 (낮음)
- 넓은 손절매 (ATR × 2.5)

### 4. LSTM Aggressive 백테스트 (공격적)

```json
{
  "strategy_type": "lstm_aggressive",
  "symbol": "BTCUSDT",
  "initial_capital": 10000.0,
  "days_back": 30
}
```

**특징**:
- 신뢰도 50% 이상에서 진입
- 리스크 5%/거래 (높음) ⚠️
- 좁은 손절매 (ATR × 1.0)

---

## 전략 비교

### 전통 전략 vs LSTM AI

**API 엔드포인트**: `POST /api/v1/backtest/compare`

```json
{
  "strategies": [
    "supertrend",
    "rsi_ema",
    "macd_stoch",
    "lstm",
    "lstm_fast"
  ],
  "symbol": "BTCUSDT",
  "initial_capital": 10000.0,
  "leverage": 3,
  "days_back": 30
}
```

**Response:**
```json
{
  "symbol": "BTCUSDT",
  "period": "30d",
  "initial_capital": 10000.0,
  "comparisons": [
    {
      "strategy_name": "LSTM-AI",
      "win_rate": 66.67,
      "total_return_pct": 15.0,
      "sharpe_ratio": 2.3,
      "max_drawdown_pct": 5.0,
      "profit_factor": 2.5,
      "total_trades": 15,
      "performance_rating": "EXCELLENT"
    },
    {
      "strategy_name": "SuperTrend",
      "win_rate": 67.0,
      "total_return_pct": 12.5,
      "sharpe_ratio": 2.0,
      "max_drawdown_pct": 6.5,
      "profit_factor": 2.2,
      "total_trades": 20,
      "performance_rating": "GOOD"
    },
    {
      "strategy_name": "RSI+EMA",
      "win_rate": 58.3,
      "total_return_pct": 8.2,
      "sharpe_ratio": 1.5,
      "max_drawdown_pct": 8.0,
      "profit_factor": 1.8,
      "total_trades": 18,
      "performance_rating": "AVERAGE"
    }
  ],
  "best_strategy": "LSTM-AI",
  "best_metric": "sharpe_ratio"
}
```

### 실시간 시그널 확인

**API 엔드포인트**: `GET /api/v1/backtest/signal/lstm`

```bash
curl "http://localhost:8001/api/v1/backtest/signal/lstm?symbol=BTCUSDT"
```

**Response:**
```json
{
  "strategy": "LSTM-AI",
  "symbol": "BTCUSDT",
  "timestamp": "2025-01-18T16:00:00",
  "current_price": 45230.50,
  "signal": {
    "should_enter": true,
    "direction": "LONG",
    "confidence": 0.72,
    "entry_price": 45230.50,
    "stop_loss": 44500.00,
    "take_profit": 46950.00,
    "reasoning": "LSTM-AI BUY: LSTM: Predicted price $45800.00 (+1.26%) | Technical: RSI=bullish, MACD=bullish, Trend=uptrend | Risk: Volatility=2.35%, Position=2.0%",
    "risk_reward_ratio": 2.35
  },
  "indicator_values": {
    "ai_signal": "BUY",
    "ai_confidence": 72.0,
    "lstm_prediction": {
      "predicted_price": 45800.00,
      "change_pct": 1.26,
      "direction": "UP"
    },
    "technical_analysis": {
      "rsi": {"value": 58.5, "signal": "bullish"},
      "macd": {"value": 120.5, "signal": "bullish"},
      "trend": {"direction": "uptrend"}
    },
    "risk_assessment": {
      "volatility": 2.35,
      "loss_probability": 28.0,
      "position_size_pct": 2.0
    }
  }
}
```

---

## 성능 최적화

### 1. 빠른 백테스팅

**문제**: Full LSTM 전략은 LLM 호출로 느림 (~10초/시그널)

**해결**:
```json
{
  "strategy_type": "lstm_fast",  // LLM 제외
  "days_back": 30
}
```

**결과**: ~3초/시그널 (3배 속도 향상)

### 2. 병렬 심볼 백테스팅

**API 엔드포인트**: `POST /api/v1/backtest/multi-symbol`

```json
{
  "strategy_type": "lstm_fast",
  "symbols": ["BTCUSDT", "ETHUSDT", "SOLUSDT", "ADAUSDT"],
  "initial_capital": 10000.0,
  "leverage": 3,
  "days_back": 30
}
```

**결과**:
```json
{
  "strategy_name": "LSTM-AI-Fast",
  "symbols": ["BTCUSDT", "ETHUSDT", "SOLUSDT", "ADAUSDT"],

  "symbol_results": [
    {"symbol": "BTCUSDT", "total_return_pct": 15.0, "win_rate": 66.67},
    {"symbol": "ETHUSDT", "total_return_pct": 12.3, "win_rate": 62.5},
    {"symbol": "SOLUSDT", "total_return_pct": 18.7, "win_rate": 70.0},
    {"symbol": "ADAUSDT", "total_return_pct": 8.5, "win_rate": 55.0}
  ],

  "portfolio_total_return_pct": 13.625,
  "portfolio_sharpe_ratio": 2.1,
  "best_performing_symbol": "SOLUSDT",
  "worst_performing_symbol": "ADAUSDT"
}
```

### 3. 모델 캐싱

LSTM 모델은 첫 로드 후 메모리에 캐싱되어 **후속 백테스트가 빠름**:

```python
# app/api/v1/ai_prediction.py (자동 캐싱)
_model_cache: Dict[str, PricePredictionLSTM] = {}
_preprocessor_cache: Dict[str, LSTMDataPreprocessor] = {}
```

**효과**:
- 첫 백테스트: ~10초 (모델 로드 + 추론)
- 후속 백테스트: ~3초 (추론만)

---

## 트러블슈팅

### 1. "Model not found" 에러

**원인**: LSTM 모델이 훈련되지 않음

**해결**:
```bash
# 모델 훈련 필수
curl -X POST "http://localhost:8001/api/v1/ai/train" \
  -H "Content-Type: application/json" \
  -d '{"symbol": "BTCUSDT", "interval": "1h", "days": 365, "epochs": 100}'

# 훈련 완료 대기 (30-60분)
# 상태 확인
curl "http://localhost:8001/api/v1/ai/model-status?symbol=BTCUSDT&interval=1h"
```

### 2. "Prediction failed" 에러

**원인**: 데이터 부족 또는 전처리 실패

**해결**:
```bash
# 충분한 데이터 확인 (최소 30일)
# 모델 재훈련
curl -X POST "http://localhost:8001/api/v1/ai/train" \
  -d '{"symbol": "BTCUSDT", "interval": "1h", "days": 365}'
```

### 3. 느린 백테스팅 성능

**원인**: LLM 분석 포함 (Llama 3.1 호출)

**해결**:
```json
{
  "strategy_type": "lstm_fast",  // LLM 제외
  "custom_params": {
    "use_llm_analysis": false
  }
}
```

### 4. 과적합 (Overfitting) 방지

**증상**: 백테스트 성과는 우수하지만 실제 거래에서 실패

**해결**:
- **Out-of-sample 테스트**: 훈련 데이터와 다른 기간으로 백테스트
- **다양한 시장 조건**: 상승장, 하락장, 횡보장에서 모두 테스트
- **교차 검증**: 여러 심볼에서 성능 확인
- **보수적 파라미터**: `lstm_conservative` 전략 사용

```json
{
  "strategy_type": "lstm_conservative",
  "days_back": 90,  // 더 긴 기간 테스트
  "custom_params": {
    "min_confidence": 75.0  // 높은 신뢰도
  }
}
```

---

## 다음 단계

### Phase 6 완료 ✅

- [x] LSTM 전략 클래스 생성 (`lstm_strategy.py`)
- [x] 백테스팅 시스템 통합 (`backtest.py`)
- [x] 4가지 전략 변형 제공 (Full, Fast, Conservative, Aggressive)
- [x] API 엔드포인트 등록 및 테스트
- [x] 전략 비교 기능 통합
- [x] 문서화 완료

### Phase 7-10 예정

- [ ] **Phase 7**: Docker 컨테이너화
- [ ] **Phase 8**: AWS 인프라 설정 (ECS, RDS, ElastiCache)
- [ ] **Phase 9**: CI/CD 파이프라인 구축
- [ ] **Phase 10**: 모니터링 및 로깅 시스템

---

## 참고 자료

- **LSTM 모델 구조**: `app/ai/lstm_model.py`
- **시그널 생성 엔진**: `app/ai/signal_generator.py`
- **백테스팅 엔진**: `app/backtesting/engine.py`
- **전략 베이스 클래스**: `app/strategies/strategies.py`

**작성일**: 2025-01-18
**버전**: 1.0.0 (Phase 6 Complete)
