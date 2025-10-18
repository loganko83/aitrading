# 🚀 BTCUSDT 선물 자동매매 Quick Start

**TradingView 웹훅 → Binance/OKX 선물 자동 주문 실행**

---

## 📊 시스템 구조

```
TradingView Pine Script (차트 분석)
         ↓
    Webhook 알림 발생
         ↓
TradingBot AI Backend (시그널 수신)
         ↓
Binance Futures / OKX Futures (주문 실행)
         ↓
    실시간 포지션 관리
```

---

## ⚡ 5분 Quick Start

### 1단계: 백엔드 실행 (3분)

```bash
cd trading-backend

# 가상환경 생성 및 활성화
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # macOS/Linux

# 패키지 설치
pip install -r requirements.txt

# 환경변수 설정 (.env 파일)
# 필수: WEBHOOK_SECRET, ENCRYPTION_KEY 생성
python -c "import secrets; print('WEBHOOK_SECRET=' + secrets.token_urlsafe(32))"
python -c "from cryptography.fernet import Fernet; print('ENCRYPTION_KEY=' + Fernet.generate_key().decode())"

# 백엔드 실행
python main.py
```

**백엔드 실행 확인**: http://localhost:8001/docs

---

### 2단계: 거래소 API 키 등록 (1분)

#### 옵션 A: API 직접 호출 (개발/테스트)

```bash
# Binance Futures Testnet API 등록
curl -X POST http://localhost:8001/api/v1/accounts/binance/register \
  -H "Content-Type: application/json" \
  -d '{
    "account_id": "my_binance_account",
    "api_key": "your_binance_testnet_api_key",
    "api_secret": "your_binance_testnet_api_secret",
    "testnet": true
  }'

# OKX Futures Demo API 등록
curl -X POST http://localhost:8001/api/v1/accounts/okx/register \
  -H "Content-Type: application/json" \
  -d '{
    "account_id": "my_okx_account",
    "api_key": "your_okx_demo_api_key",
    "api_secret": "your_okx_demo_api_secret",
    "passphrase": "your_okx_passphrase",
    "testnet": true
  }'
```

#### 옵션 B: 프론트엔드 UI (프로덕션)

1. http://localhost:3000 접속
2. 로그인
3. "계정 관리" → "거래소 API 등록"
4. API 키 입력 (AES-256 암호화 저장)

---

### 3단계: TradingView 설정 (1분)

#### 3.1 Pine Script 추가

1. TradingView 접속: https://www.tradingview.com
2. **Binance Futures: BTCUSDT** 차트 열기 (중요: Futures 차트!)
3. 하단 "Pine Editor" 클릭
4. `pine_scripts/btcusdt_simple_strategy.pine` 내용 복사/붙여넣기
5. "차트에 추가" 클릭

#### 3.2 파라미터 설정

- **Account ID**: `my_binance_account` (2단계에서 등록한 ID)
- **Webhook Secret**: `.env` 파일의 `WEBHOOK_SECRET` 값
- **Leverage**: `3` (기본값)

#### 3.3 웹훅 알림 생성

1. 차트에서 "알림" 아이콘 클릭
2. 조건: "BTCUSDT Simple Webhook Strategy" 선택
3. **Webhook URL**: `http://your-server-ip:8001/api/v1/webhook/tradingview`
   - 로컬 테스트: `http://localhost:8001/api/v1/webhook/tradingview`
   - 프로덕션: `https://your-domain.com/api/v1/webhook/tradingview` (HTTPS 권장)
4. **메시지**: `{{strategy.order.alert_syntax}}` 입력
5. "생성" 클릭

---

## 🎯 BTCUSDT 전용 설정

### Binance Futures

**심볼**: `BTCUSDT` (Perpetual Futures)
**최소 주문 수량**: 0.001 BTC
**레버리지**: 1x ~ 125x
**테스트넷**: https://testnet.binancefuture.com

### OKX Futures

**심볼**: `BTC-USDT-SWAP` (Perpetual Swap)
**최소 주문 수량**: 1 Cont (= 0.01 BTC)
**레버리지**: 1x ~ 125x
**데모 트레이딩**: https://www.okx.com/demo-trading

---

## 📋 Webhook JSON 형식

### 롱 진입 (Long Entry)

```json
{
  "account_id": "my_binance_account",
  "exchange": "binance",
  "action": "long",
  "symbol": "BTCUSDT",
  "leverage": 3,
  "secret": "your_webhook_secret",
  "timestamp": 1705536000
}
```

### 숏 진입 (Short Entry)

```json
{
  "account_id": "my_binance_account",
  "exchange": "binance",
  "action": "short",
  "symbol": "BTCUSDT",
  "leverage": 3,
  "secret": "your_webhook_secret",
  "timestamp": 1705536000
}
```

### 롱 포지션 청산 (Close Long)

```json
{
  "account_id": "my_binance_account",
  "exchange": "binance",
  "action": "close_long",
  "symbol": "BTCUSDT",
  "secret": "your_webhook_secret",
  "timestamp": 1705536000
}
```

### 숏 포지션 청산 (Close Short)

```json
{
  "account_id": "my_binance_account",
  "exchange": "binance",
  "action": "close_short",
  "symbol": "BTCUSDT",
  "secret": "your_webhook_secret",
  "timestamp": 1705536000
}
```

### 모든 포지션 청산 (Close All)

```json
{
  "account_id": "my_binance_account",
  "exchange": "binance",
  "action": "close_all",
  "symbol": "BTCUSDT",
  "secret": "your_webhook_secret",
  "timestamp": 1705536000
}
```

---

## 🔧 고급 설정

### 레버리지 변경

```json
{
  "leverage": 5  // 1x ~ 125x
}
```

### 수동 수량 지정

```json
{
  "quantity": 0.01  // BTC 단위
}
```

### Stop Loss / Take Profit

```json
{
  "stop_loss": 65000,
  "take_profit": 75000
}
```

---

## 🎯 Pine Script 전략 예시

### 1. 단순 EMA 크로스

```pine
fastEMA = ta.ema(close, 9)
slowEMA = ta.ema(close, 21)

longCondition = ta.crossover(fastEMA, slowEMA)
shortCondition = ta.crossunder(fastEMA, slowEMA)
```

### 2. RSI + 볼린저 밴드

```pine
rsi = ta.rsi(close, 14)
[middle, upper, lower] = ta.bb(close, 20, 2)

longCondition = rsi < 30 and close < lower
shortCondition = rsi > 70 and close > upper
```

### 3. MACD + Volume

```pine
[macdLine, signalLine, _] = ta.macd(close, 12, 26, 9)
volumeAvg = ta.sma(volume, 20)

longCondition = ta.crossover(macdLine, signalLine) and volume > volumeAvg
shortCondition = ta.crossunder(macdLine, signalLine) and volume > volumeAvg
```

---

## ⚠️ 안전 수칙

### 테스트넷 필수

```bash
# Binance Futures Testnet
BINANCE_TESTNET=True

# OKX Demo Trading
# https://www.okx.com/demo-trading
```

### API 키 권한 최소화

- ✅ **Enable Futures**: 허용
- ❌ **Enable Withdrawals**: 금지 (반드시 비활성화!)

### IP 화이트리스트

- Binance: API 관리 → IP 제한 활성화
- OKX: API 관리 → IP 화이트리스트 추가

### 포지션 크기 제한

```python
# 백엔드 설정 (.env)
MAX_POSITION_SIZE_PCT=0.10  # 계좌의 최대 10%만 사용
```

---

## 📊 실시간 모니터링

### 백엔드 로그

```bash
# 실시간 로그 확인
tail -f logs/app.log

# 에러 로그
tail -f logs/error.log

# 보안 이벤트
tail -f logs/security.log
```

### API 상태 확인

```bash
# 헬스체크
curl http://localhost:8001/api/v1/webhook/health

# 응답 예시:
{
  "status": "healthy",
  "service": "TradingView Webhook Receiver",
  "registered_accounts": {
    "binance": 1,
    "okx": 1
  }
}
```

---

## 🆘 문제 해결

### Webhook이 작동하지 않을 때

1. **백엔드 로그 확인**:
   ```bash
   tail -f logs/app.log | grep webhook
   ```

2. **Secret 검증 실패**:
   - `.env` 파일의 `WEBHOOK_SECRET`와 Pine Script의 `webhook_secret`이 동일한지 확인

3. **타임스탬프 에러**:
   - Pine Script에 `"timestamp":' + str.tostring(timenow / 1000)` 포함 확인

4. **계정 ID 오류**:
   - `account_id`가 2단계에서 등록한 ID와 정확히 일치하는지 확인

### 주문이 실행되지 않을 때

1. **API 키 확인**:
   ```bash
   curl http://localhost:8001/api/v1/accounts/my_binance_account/status
   ```

2. **거래소 API 권한**:
   - Futures 거래 권한 활성화 확인

3. **잔고 부족**:
   - 테스트넷 계정 잔고 충전

---

## 📚 관련 문서

- **[TRADINGVIEW_WEBHOOK_GUIDE.md](trading-backend/TRADINGVIEW_WEBHOOK_GUIDE.md)** - 상세 웹훅 가이드
- **[SECURITY.md](trading-backend/SECURITY.md)** - 보안 강화 가이드
- **[CLAUDE.md](trading-backend/CLAUDE.md)** - 전체 시스템 아키텍처

---

## 💡 추천 TradingView 설정

### 차트

- **거래소**: Binance Futures
- **심볼**: BTCUSDT
- **타임프레임**: 15분 (단타) / 1시간 (스윙)

### 지표

- EMA(9, 21, 50, 200)
- RSI(14)
- MACD(12, 26, 9)
- Bollinger Bands(20, 2)

### 알림

- **빈도**: "알림 발생 시 한 번만" 또는 "봉 마감 시 한 번만"
- **만료**: 무제한 또는 1개월

---

**BTCUSDT 선물 자동매매 시작!** 🚀📈

**⚠️ 주의**: 반드시 테스트넷에서 충분히 테스트 후 실전 운영하세요!
