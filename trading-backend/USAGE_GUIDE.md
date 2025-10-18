# TradingBot AI Backend - 사용 가이드

## 📋 목차

1. [시스템 개요](#시스템-개요)
2. [Simple API 사용법 (초보자 권장)](#simple-api-사용법)
3. [거래소별 최적화 설정](#거래소별-최적화-설정)
4. [안정성 기능](#안정성-기능)
5. [헬스 모니터링](#헬스-모니터링)
6. [Advanced API](#advanced-api)
7. [에러 처리](#에러-처리)

---

## 시스템 개요

TradingBot AI Backend는 **사용자 중심**, **단순성**, **안정성**, **최적화**를 핵심 가치로 설계되었습니다.

### 주요 기능

✅ **원클릭 백테스팅** - 프리셋 선택만으로 즉시 백테스트 실행
✅ **AI 기반 추천** - 자본금, 경험, 리스크 성향에 맞는 자동 추천
✅ **거래소 최적화** - Binance와 OKX에 최적화된 설정
✅ **안정성 보장** - 자동 재시도, 타임아웃, 서킷 브레이커
✅ **실시간 모니터링** - 시스템 상태 실시간 확인

---

## Simple API 사용법

Simple API는 **3단계로 트레이딩을 시작**할 수 있도록 설계되었습니다.

### 1단계: 프리셋 목록 조회

```bash
GET /api/v1/presets
```

**응답 예시:**

```json
[
  {
    "id": "beginner_safe",
    "name": "Beginner Safe",
    "name_ko": "초보자 안전 모드",
    "description_ko": "처음 트레이딩하는 분들을 위한 설정. 낮은 리스크, 간단한 전략.",
    "category": "beginner",
    "difficulty": "Easy",
    "time_commitment": "Low",
    "expected_win_rate": "45-55%",
    "expected_return_monthly": "3-8%",
    "recommended_capital_min": 500.0,
    "leverage": 1,
    "position_size_pct": 0.05
  },
  {
    "id": "balanced_trader",
    "name": "Balanced Trader",
    "name_ko": "균형잡힌 트레이더",
    "description_ko": "리스크와 수익의 균형. 가장 인기있는 선택.",
    "category": "balanced",
    "difficulty": "Medium",
    "expected_win_rate": "55-65%",
    "expected_return_monthly": "10-20%",
    "recommended_capital_min": 2000.0
  }
]
```

### 2단계: AI 스마트 추천 (선택사항)

```bash
POST /api/v1/recommend
Content-Type: application/json

{
  "capital": 5000,
  "experience_level": "beginner",
  "risk_tolerance": "low",
  "exchange": "binance"
}
```

**응답 예시:**

```json
{
  "recommended_preset": {
    "id": "beginner_safe",
    "name_ko": "초보자 안전 모드",
    "leverage": 1,
    "expected_return_monthly": "3-8%"
  },
  "reasoning": "Based on your beginner level and low risk tolerance...",
  "reasoning_ko": "트레이딩 초보자이고 낮은 리스크를 선호하시네요. '초보자 안전 모드'를 추천드립니다.",
  "warnings": [
    "⚠️ 추천 최소 자본금은 $500입니다. 현재 자본금은 충분합니다."
  ],
  "tips": [
    "💡 추천 심볼: BTCUSDT, ETHUSDT",
    "💡 추천 타임프레임: 1h, 4h",
    "💡 예상 월 수익률: 3-8% (안정적)",
    "💡 레버리지: 1배 (안전)"
  ]
}
```

### 3단계: 원클릭 백테스트 실행

```bash
POST /api/v1/quick-backtest
Content-Type: application/json

{
  "preset_id": "beginner_safe",
  "exchange": "binance",
  "symbol": "BTCUSDT",  // 선택사항 (생략시 프리셋 기본값)
  "days_back": 30,
  "initial_capital": 5000
}
```

**응답 예시:**

```json
{
  "success": true,
  "preset_info": {
    "name_ko": "초보자 안전 모드",
    "expected_win_rate": "45-55%",
    "difficulty": "Easy"
  },
  "backtest_result": {
    "total_return": 8.5,
    "win_rate": 52.3,
    "total_trades": 23,
    "sharpe_ratio": 1.45,
    "max_drawdown": 5.2
  },
  "performance_vs_expected": {
    "return_status": "✅ 예상 범위 내 (3-8%)",
    "win_rate_status": "✅ 예상 범위 내 (45-55%)"
  }
}
```

---

## 거래소별 최적화 설정

### Binance와 OKX의 차이점

| 항목 | Binance | OKX |
|------|---------|-----|
| **수수료 (기본)** | Maker 0.02%, Taker 0.04% | Maker 0.02%, Taker 0.05% |
| **최소 주문 금액** | $5 | $1 |
| **심볼 형식** | BTCUSDT | BTC-USDT |
| **최대 레버리지** | 125x | 125x |
| **API 속도 제한** | 2400/min | 1200/min |

### 거래소 정보 조회

```bash
GET /api/v1/exchanges/binance?mode=futures
```

**응답:**

```json
{
  "exchange": "binance",
  "mode": "futures",
  "fees": {
    "maker_fee": 0.0002,
    "taker_fee": 0.0004,
    "vip_levels": {
      "0": {"maker": 0.0002, "taker": 0.0004},
      "1": {"maker": 0.00016, "taker": 0.0004}
    }
  },
  "limits": {
    "max_leverage": 125,
    "min_order_size": 5.0,
    "max_order_size": 1000000.0,
    "api_rate_limit": 2400
  },
  "optimal_symbols": ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT"],
  "optimal_timeframes": ["5m", "15m", "1h", "4h"]
}
```

### VIP 레벨 수수료 적용

VIP 레벨이 있는 경우 자동으로 할인된 수수료가 적용됩니다:

```bash
GET /api/v1/exchanges/binance?mode=futures&vip_level=1
```

---

## 안정성 기능

### 1. 자동 재시도 (Automatic Retry)

모든 API 호출은 **자동으로 재시도**됩니다:

- **최대 재시도 횟수**: 3-5회
- **재시도 전략**: Exponential Backoff (지수 백오프)
- **재시도 간격**: 1초 → 2초 → 4초 → 8초...
- **Jitter 적용**: 동시 요청 방지를 위한 랜덤 지연

**예시:**

```
1차 시도 실패 → 1.2초 대기 → 2차 시도
2차 시도 실패 → 2.5초 대기 → 3차 시도
3차 시도 실패 → 4.8초 대기 → 4차 시도
4차 시도 성공 ✅
```

### 2. 타임아웃 보호 (Timeout Protection)

모든 API 호출에 **타임아웃 설정**:

- **기본 타임아웃**: 30초
- **긴 작업**: 60초
- **타임아웃 시**: 자동 재시도 또는 에러 반환

### 3. 서킷 브레이커 (Circuit Breaker)

**장애 확산 방지**를 위한 서킷 브레이커:

#### 작동 원리

```
CLOSED (정상) → 5회 연속 실패 → OPEN (차단)
OPEN → 60초 대기 → HALF_OPEN (테스트)
HALF_OPEN → 2회 성공 → CLOSED (복구)
HALF_OPEN → 1회 실패 → OPEN (재차단)
```

#### 서킷 브레이커 상태 확인

```bash
GET /api/v1/health/circuit-breakers
```

**응답:**

```json
[
  {
    "name": "binance_api",
    "state": "closed",
    "failure_count": 0,
    "success_count": 125,
    "health_percentage": 100.0,
    "last_state_change": "2025-10-18T10:30:00"
  },
  {
    "name": "okx_api",
    "state": "half_open",
    "failure_count": 0,
    "success_count": 1,
    "health_percentage": 50.0,
    "next_retry_time": null
  }
]
```

#### 서킷 브레이커 수동 리셋

```bash
POST /api/v1/health/circuit-breakers/reset
Content-Type: application/json

{
  "breaker_name": "binance_api"  // null이면 전체 리셋
}
```

---

## 헬스 모니터링

### 종합 시스템 상태 확인

```bash
GET /api/v1/health
```

**응답 예시:**

```json
{
  "status": "healthy",
  "message": "모든 시스템이 정상 작동 중입니다.",
  "timestamp": "2025-10-18T12:00:00",
  "services": [
    {
      "name": "database",
      "status": "healthy",
      "message": "Service is operating normally"
    },
    {
      "name": "binance_api",
      "status": "healthy",
      "message": "Service is operating normally"
    },
    {
      "name": "okx_api",
      "status": "degraded",
      "message": "High latency detected"
    }
  ],
  "circuit_breakers": [
    {
      "name": "binance_api",
      "state": "closed",
      "health_percentage": 100.0
    }
  ],
  "system_metrics": {
    "cpu_percent": 25.5,
    "memory_percent": 45.2,
    "disk_percent": 60.1,
    "uptime_seconds": 86400
  },
  "warnings": [
    "⚠️ OKX API 응답 시간이 느립니다."
  ],
  "recommendations": [
    "✅ 시스템이 안정적으로 작동하고 있습니다."
  ]
}
```

### 시스템 리소스만 조회

```bash
GET /api/v1/health/metrics
```

**응답:**

```json
{
  "cpu_percent": 25.5,
  "memory_percent": 45.2,
  "disk_percent": 60.1,
  "uptime_seconds": 86400
}
```

---

## Advanced API

### 수동 백테스트 (세밀한 파라미터 제어)

```bash
POST /api/v1/backtest
Content-Type: application/json

{
  "strategy_type": "supertrend",
  "symbol": "BTCUSDT",
  "timeframe": "1h",
  "leverage": 3,
  "position_size_pct": 0.10,
  "atr_sl_multiplier": 1.5,
  "atr_tp_multiplier": 3.0,
  "max_open_positions": 3,
  "max_daily_loss_pct": 0.05,
  "max_drawdown_pct": 0.20,
  "maker_fee": 0.0002,
  "taker_fee": 0.0004,
  "custom_params": {
    "period": 10,
    "multiplier": 3.0
  }
}
```

### Pine Script 변환

TradingView Pine Script를 Python으로 자동 변환:

```bash
POST /api/v1/import-pine-script
Content-Type: application/json

{
  "pine_script_code": "//@version=5\nindicator(\"My Custom Indicator\")\n...",
  "indicator_name": "MyCustomIndicator"
}
```

**응답:**

```json
{
  "success": true,
  "message": "Pine Script가 성공적으로 Python으로 변환되었습니다!",
  "python_code": "def my_custom_indicator(df: pd.DataFrame, period: int = 14):\n    ...",
  "function_name": "my_custom_indicator",
  "parameters": {
    "period": 14
  },
  "usage_example": "# indicators.py에 추가:\n..."
}
```

---

## 에러 처리

### 에러 타입

| 에러 타입 | HTTP 코드 | 설명 | 재시도 |
|----------|-----------|------|--------|
| `ValidationError` | 400 | 잘못된 입력 파라미터 | ❌ |
| `RateLimitError` | 429 | API 속도 제한 초과 | ✅ (30초 후) |
| `NetworkError` | 503 | 네트워크 연결 오류 | ✅ (자동) |
| `CircuitBreakerOpenError` | 503 | 서킷 브레이커 OPEN | ❌ (60초 후 자동 복구) |
| `AuthenticationError` | 401 | 인증 실패 | ❌ |
| `ExchangeError` | 500 | 거래소 내부 오류 | ✅ (자동) |

### 에러 응답 예시

```json
{
  "detail": "Circuit breaker for binance is OPEN. Will retry at 2025-10-18 12:05:00",
  "error_type": "CircuitBreakerOpenError",
  "retry_after": 60,
  "recommendations": [
    "시스템이 자동으로 복구를 시도합니다.",
    "60초 후 다시 시도하거나, /health/circuit-breakers/reset으로 수동 리셋하세요."
  ]
}
```

---

## 프론트엔드 통합 예시

### React Example

```typescript
// API 클라이언트 설정
const API_BASE = 'http://localhost:8001/api/v1';

// 1. 프리셋 목록 조회
async function getPresets() {
  const response = await fetch(`${API_BASE}/presets`);
  return await response.json();
}

// 2. AI 추천 받기
async function getRecommendation(capital: number, experience: string, risk: string) {
  const response = await fetch(`${API_BASE}/recommend`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      capital,
      experience_level: experience,
      risk_tolerance: risk,
      exchange: 'binance'
    })
  });
  return await response.json();
}

// 3. 원클릭 백테스트
async function runBacktest(presetId: string, capital: number) {
  const response = await fetch(`${API_BASE}/quick-backtest`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      preset_id: presetId,
      exchange: 'binance',
      days_back: 30,
      initial_capital: capital
    })
  });
  return await response.json();
}

// 4. 시스템 상태 확인
async function checkHealth() {
  const response = await fetch(`${API_BASE}/health`);
  return await response.json();
}

// 사용 예시
const App = () => {
  const [presets, setPresets] = useState([]);
  const [health, setHealth] = useState(null);

  useEffect(() => {
    // 프리셋 목록 로드
    getPresets().then(setPresets);

    // 5초마다 시스템 상태 확인
    const interval = setInterval(() => {
      checkHealth().then(setHealth);
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  return (
    <div>
      <SystemHealth status={health} />
      <PresetSelector presets={presets} />
      <BacktestResults />
    </div>
  );
};
```

---

## 성능 최적화 팁

### 1. 프리셋 활용

❌ **비효율적:**

```javascript
// 매번 10개 이상의 파라미터 전송
await fetch('/api/v1/backtest', {
  body: JSON.stringify({
    strategy_type: "supertrend",
    leverage: 3,
    position_size_pct: 0.10,
    // ... 7개 더
  })
});
```

✅ **효율적:**

```javascript
// 프리셋 ID만 전송
await fetch('/api/v1/quick-backtest', {
  body: JSON.stringify({
    preset_id: "balanced_trader",
    initial_capital: 5000
  })
});
```

### 2. 시스템 상태 캐싱

```javascript
// 5초마다만 확인 (너무 자주 확인하지 말 것)
const interval = setInterval(checkHealth, 5000);
```

### 3. 에러 재시도 로직

```javascript
async function safeApiCall(apiFunction, maxRetries = 3) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await apiFunction();
    } catch (error) {
      if (error.error_type === 'CircuitBreakerOpenError') {
        // 서킷 브레이커 OPEN - 재시도 금지
        throw error;
      }
      if (i === maxRetries - 1) throw error;
      await new Promise(resolve => setTimeout(resolve, 1000 * (i + 1)));
    }
  }
}
```

---

## 보안 가이드

### API 키 관리

```bash
# .env 파일 (절대 커밋하지 말 것!)
BINANCE_API_KEY=your_api_key_here
BINANCE_API_SECRET=your_api_secret_here
OKX_API_KEY=your_okx_key
OKX_API_SECRET=your_okx_secret
```

### CORS 설정

프론트엔드 도메인을 허용 목록에 추가:

```python
# main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # 개발 환경
        "https://yourdomain.com"  # 프로덕션 환경
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 문의 및 지원

문제가 발생하거나 질문이 있으시면:

1. **시스템 상태 확인**: `GET /api/v1/health`
2. **서킷 브레이커 상태 확인**: `GET /api/v1/health/circuit-breakers`
3. **로그 확인**: `trading-backend/logs/`
4. **수동 복구**: `POST /api/v1/health/circuit-breakers/reset`

---

## 버전 정보

- **API Version**: 1.0.0
- **안정성 기능**: ✅ 완전 활성화
  - Retry Logic: ✅
  - Circuit Breaker: ✅
  - Timeout Protection: ✅
  - Graceful Degradation: ✅
