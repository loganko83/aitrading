# ⚡ BTCUSDT Futures 자동매매 5분 빠른 시작

**TradingView 시그널** → **AI 분석** → **Binance/OKX Futures 주문** → **텔레그램 알림**

---

## 🎯 시스템 아키텍처

```
┌─────────────────┐     ┌──────────────┐     ┌─────────────────┐
│  TradingView    │────▶│   Backend    │────▶│ Binance Futures │
│  Pine Script    │     │  AI Ensemble │     │  OKX Futures    │
│  (시그널 생성)   │     │  (분석 & 실행)│     │  (주문 체결)     │
└─────────────────┘     └──────────────┘     └─────────────────┘
                              │
                              ▼
                        ┌──────────────┐
                        │  Telegram    │
                        │  (실시간 알림)│
                        └──────────────┘
```

---

## 🚀 3단계 설정

### Step 1: 백엔드 실행 (1분)

```bash
# 1. 환경변수 설정
cp .env.example .env
# .env 파일 열어서 다음 항목 설정:
# - BINANCE_API_KEY, BINANCE_API_SECRET
# - WEBHOOK_SECRET (랜덤 문자열 32자 이상)
# - TELEGRAM_BOT_TOKEN (선택사항)

# 2. 데이터베이스 마이그레이션
alembic upgrade head

# 3. 서버 실행
python main.py
# 서버 주소: http://localhost:8001
# API 문서: http://localhost:8001/docs
```

### Step 2: API 키 등록 (2분)

#### Binance Futures Testnet

```bash
# 1. Binance Testnet 가입
# https://testnet.binancefuture.com

# 2. API 키 생성
# - 로그인 → API Management → Create API Key
# - Futures 권한 활성화
# - IP 화이트리스트 설정 (선택사항)

# 3. 백엔드에 API 키 등록
curl -X POST http://localhost:8001/api/v1/accounts/register \
  -H "Content-Type: application/json" \
  -d '{
    "account_id": "my_binance_testnet",
    "exchange": "binance",
    "api_key": "YOUR_BINANCE_TESTNET_API_KEY",
    "api_secret": "YOUR_BINANCE_TESTNET_SECRET",
    "testnet": true
  }'

# ✅ 성공 응답 예시:
# {
#   "account_id": "my_binance_testnet",
#   "exchange": "binance",
#   "is_active": true,
#   "testnet": true
# }
```

#### OKX Futures (선택사항)

```bash
# 1. OKX Demo Trading 가입
# https://www.okx.com/demo-trading

# 2. API 키 생성 (Passphrase 필수)

# 3. 백엔드에 API 키 등록
curl -X POST http://localhost:8001/api/v1/accounts/register \
  -H "Content-Type: application/json" \
  -d '{
    "account_id": "my_okx_demo",
    "exchange": "okx",
    "api_key": "YOUR_OKX_API_KEY",
    "api_secret": "YOUR_OKX_SECRET",
    "passphrase": "YOUR_OKX_PASSPHRASE",
    "testnet": true
  }'
```

### Step 3: TradingView 설정 (2분)

#### 3-1. Pine Script 전략 생성

```pine
//@version=5
strategy("BTCUSDT Simple Webhook Strategy", overlay=true, initial_capital=10000)

// ==================== 설정 파라미터 ====================
fastLength = input.int(9, "Fast EMA", minval=1)
slowLength = input.int(21, "Slow EMA", minval=1)
leverage = input.int(3, "Leverage", minval=1, maxval=125)

// Webhook 설정 (본인의 값으로 변경!)
account_id = input.string("my_binance_testnet", "Account ID")
webhook_secret = input.string("your_webhook_secret_here", "Webhook Secret")

// ==================== 전략 로직 ====================
fastEMA = ta.ema(close, fastLength)
slowEMA = ta.ema(close, slowLength)

// 진입 조건
longCondition = ta.crossover(fastEMA, slowEMA)
shortCondition = ta.crossunder(fastEMA, slowEMA)

// 차트에 EMA 표시
plot(fastEMA, "Fast EMA", color=color.blue, linewidth=2)
plot(slowEMA, "Slow EMA", color=color.red, linewidth=2)

// ==================== 주문 실행 ====================

// 롱 진입
if (longCondition and strategy.position_size == 0)
    strategy.entry("Long", strategy.long)

    // Webhook 알림 전송 (JSON 형식)
    alert('{"account_id":"' + account_id + '","exchange":"binance","action":"long","symbol":"BTCUSDT","leverage":' + str.tostring(leverage) + ',"secret":"' + webhook_secret + '","timestamp":' + str.tostring(timenow / 1000) + '}', alert.freq_once_per_bar_close)

// 숏 진입
if (shortCondition and strategy.position_size == 0)
    strategy.entry("Short", strategy.short)

    // Webhook 알림 전송
    alert('{"account_id":"' + account_id + '","exchange":"binance","action":"short","symbol":"BTCUSDT","leverage":' + str.tostring(leverage) + ',"secret":"' + webhook_secret + '","timestamp":' + str.tostring(timenow / 1000) + '}', alert.freq_once_per_bar_close)

// 청산 (반대 시그널 발생 시)
if (shortCondition and strategy.position_size > 0)
    strategy.close("Long")
    alert('{"account_id":"' + account_id + '","exchange":"binance","action":"close_long","symbol":"BTCUSDT","secret":"' + webhook_secret + '","timestamp":' + str.tostring(timenow / 1000) + '}', alert.freq_once_per_bar_close)

if (longCondition and strategy.position_size < 0)
    strategy.close("Short")
    alert('{"account_id":"' + account_id + '","exchange":"binance","action":"close_short","symbol":"BTCUSDT","secret":"' + webhook_secret + '","timestamp":' + str.tostring(timenow / 1000) + '}', alert.freq_once_per_bar_close)
```

#### 3-2. TradingView 알림 생성

1. **차트에 전략 적용**
   - Pine Editor에서 위 코드 복사
   - "Add to chart" 클릭

2. **알림 생성**
   - 차트 우측 상단 "알림" 아이콘 클릭
   - "생성" 버튼 클릭

3. **알림 설정**
   ```
   조건: BTCUSDT Simple Webhook Strategy
   옵션: alert() function calls only
   Webhook URL: http://YOUR_SERVER_IP:8001/api/v1/webhook/tradingview
   (로컬 테스트: http://localhost:8001/api/v1/webhook/tradingview)
   ```

4. **Ngrok으로 로컬 서버 공개 (로컬 개발 시)**
   ```bash
   # Ngrok 설치 (https://ngrok.com)
   ngrok http 8001

   # Ngrok URL 복사 (예: https://abcd1234.ngrok.io)
   # Webhook URL: https://abcd1234.ngrok.io/api/v1/webhook/tradingview
   ```

5. **알림 저장**
   - "생성" 클릭

---

## 📊 BTCUSDT 전용 설정

### Binance Futures BTCUSDT 설정

```python
# 심볼: BTCUSDT
# 타입: USDT-M 영구 선물
# 틱 사이즈: 0.1 USDT
# 최소 주문: 0.001 BTC
# 레버리지: 1x ~ 125x

# 권장 설정 (.env)
DEFAULT_LEVERAGE=3              # 보수적 레버리지
MAX_POSITION_SIZE_PCT=0.10      # 계좌의 10%만 사용
ATR_PERIOD=14                   # ATR 기반 포지션 사이징
```

### OKX Futures BTC-USDT-SWAP 설정

```python
# 심볼: BTC-USDT-SWAP
# 타입: 영구 스왑
# 틱 사이즈: 0.1 USDT
# 최소 주문: 1 계약 (0.01 BTC)
# 레버리지: 1x ~ 125x

# OKX는 Passphrase 필수!
```

---

## 🔔 텔레그램 알림 설정 (선택사항, 3분)

> 자세한 가이드: [TELEGRAM_SETUP_GUIDE.md](TELEGRAM_SETUP_GUIDE.md)

```bash
# 1. @BotFather에서 봇 생성
# 2. 봇 토큰을 .env에 추가
TELEGRAM_BOT_TOKEN="123456789:ABCdefGHIjkl..."

# 3. 백엔드 재시작
python main.py

# 4. @userinfobot에서 채팅 ID 확인
# 5. 채팅 ID 등록
curl -X POST http://localhost:8001/api/v1/telegram/register \
  -H "Content-Type: application/json" \
  -d '{
    "account_id": "my_binance_testnet",
    "telegram_chat_id": "123456789"
  }'

# 6. 테스트 알림
curl -X POST http://localhost:8001/api/v1/telegram/test \
  -H "Content-Type: application/json" \
  -d '{"account_id": "my_binance_testnet"}'
```

**알림 종류**:
- 🚀 롱/숏 진입 (즉시 알림)
- ✅ 포지션 청산 (즉시 알림)
- 📊 손익 업데이트 (1% 이상 변화 시)
- 📡 Webhook 수신 확인
- ⚠️ 에러 발생 (즉시 알림)

---

## 🧪 테스트 및 검증

### 1. Webhook 수동 테스트

```bash
# 롱 진입 테스트
curl -X POST http://localhost:8001/api/v1/webhook/tradingview \
  -H "Content-Type: application/json" \
  -d '{
    "account_id": "my_binance_testnet",
    "exchange": "binance",
    "action": "long",
    "symbol": "BTCUSDT",
    "leverage": 3,
    "secret": "your_webhook_secret_here",
    "timestamp": 1704067200
  }'

# ✅ 성공 응답:
# {
#   "success": true,
#   "message": "LONG order executed on binance",
#   "order_details": {
#     "orderId": "12345678",
#     "symbol": "BTCUSDT",
#     "side": "BUY",
#     "quantity": 0.01
#   }
# }
```

### 2. TradingView 시그널 테스트

```
1. TradingView 차트 열기 (BTCUSDT, 5분봉)
2. Pine Script 전략 실행
3. EMA 크로스오버 발생 대기
4. 백엔드 로그 확인:
   tail -f logs/app.log

5. 텔레그램 알림 확인
6. Binance Testnet에서 포지션 확인
```

### 3. 로그 모니터링

```bash
# 전체 로그
tail -f logs/app.log

# 에러만 확인
tail -f logs/error.log

# 보안 이벤트
tail -f logs/security.log

# Webhook 이벤트만 필터링
tail -f logs/app.log | grep "Webhook"
```

---

## 📈 Pine Script 전략 예시

### 1. EMA Crossover (기본)

```pine
// 빠른 EMA가 느린 EMA를 상향 돌파 → 롱
// 빠른 EMA가 느린 EMA를 하향 돌파 → 숏

fastEMA = ta.ema(close, 9)
slowEMA = ta.ema(close, 21)

longCondition = ta.crossover(fastEMA, slowEMA)
shortCondition = ta.crossunder(fastEMA, slowEMA)
```

### 2. RSI Overbought/Oversold

```pine
// RSI < 30 → 과매도 (롱 진입)
// RSI > 70 → 과매수 (숏 진입)

rsiValue = ta.rsi(close, 14)

longCondition = ta.crossover(rsiValue, 30)
shortCondition = ta.crossunder(rsiValue, 70)
```

### 3. MACD Signal

```pine
// MACD가 시그널선을 상향 돌파 → 롱
// MACD가 시그널선을 하향 돌파 → 숏

[macdLine, signalLine, _] = ta.macd(close, 12, 26, 9)

longCondition = ta.crossover(macdLine, signalLine)
shortCondition = ta.crossunder(macdLine, signalLine)
```

### 4. Bollinger Bands Breakout

```pine
// 가격이 하단 밴드 하향 돌파 → 롱 (반등 기대)
// 가격이 상단 밴드 상향 돌파 → 숏 (조정 기대)

[middle, upper, lower] = ta.bb(close, 20, 2)

longCondition = ta.crossunder(close, lower)
shortCondition = ta.crossover(close, upper)
```

---

## 📊 Webhook JSON 형식

### 롱 진입

```json
{
  "account_id": "my_binance_testnet",
  "exchange": "binance",
  "action": "long",
  "symbol": "BTCUSDT",
  "leverage": 3,
  "price": 67500.0,
  "quantity": 0.01,
  "secret": "your_webhook_secret_here",
  "timestamp": 1704067200
}
```

### 숏 진입

```json
{
  "account_id": "my_binance_testnet",
  "exchange": "binance",
  "action": "short",
  "symbol": "BTCUSDT",
  "leverage": 3,
  "secret": "your_webhook_secret_here",
  "timestamp": 1704067200
}
```

### 롱 포지션 청산

```json
{
  "account_id": "my_binance_testnet",
  "exchange": "binance",
  "action": "close_long",
  "symbol": "BTCUSDT",
  "secret": "your_webhook_secret_here",
  "timestamp": 1704067200
}
```

### 모든 포지션 청산

```json
{
  "account_id": "my_binance_testnet",
  "exchange": "binance",
  "action": "close_all",
  "symbol": "BTCUSDT",
  "secret": "your_webhook_secret_here",
  "timestamp": 1704067200
}
```

---

## 🛡️ 안전 규칙

### 1. Testnet 먼저 테스트
```
⚠️ 실제 자금을 사용하기 전에 최소 1주일 이상 Testnet에서 테스트하세요!
```

### 2. 레버리지 낮게 시작
```
✅ 권장: 1x ~ 3x (초보자)
⚠️ 주의: 5x ~ 10x (중급자)
❌ 위험: 10x 이상 (고급자)
```

### 3. 포지션 사이즈 제한
```python
# .env 설정
MAX_POSITION_SIZE_PCT=0.10  # 계좌의 10%만 사용
DEFAULT_LEVERAGE=3          # 기본 레버리지 3배
```

### 4. 손절매 필수 설정
```pine
// Pine Script에서 손절매 설정
strategy.exit("Stop Loss", "Long", stop=entry_price * 0.98)  // -2% 손절
```

### 5. 정기적 모니터링
```
- 매일 포지션 확인
- 주간 성과 분석
- 월간 전략 검토
```

---

## 🆘 문제 해결

### "Invalid webhook secret"

```bash
# .env의 WEBHOOK_SECRET과 Pine Script의 webhook_secret이 일치하는지 확인
# 백엔드 재시작
python main.py
```

### "Account not found"

```bash
# API 키가 등록되었는지 확인
curl http://localhost:8001/api/v1/accounts/my_binance_testnet

# 없으면 다시 등록
curl -X POST http://localhost:8001/api/v1/accounts/register ...
```

### "Insufficient balance"

```
1. Binance Testnet에서 잔고 확인
2. Testnet Faucet에서 테스트 자금 받기
3. 포지션 사이즈 줄이기 (MAX_POSITION_SIZE_PCT 감소)
```

### "Telegram notification not sent"

```bash
# 1. 봇 토큰 확인
cat .env | grep TELEGRAM_BOT_TOKEN

# 2. 채팅 ID 확인
curl http://localhost:8001/api/v1/telegram/my_binance_testnet

# 3. 봇과 대화 시작 (/start)
# 4. 테스트 알림 재전송
curl -X POST http://localhost:8001/api/v1/telegram/test ...
```

---

## 📚 추가 자료

- **전체 문서**: [README.md](README.md)
- **텔레그램 설정**: [TELEGRAM_SETUP_GUIDE.md](TELEGRAM_SETUP_GUIDE.md)
- **보안 가이드**: [SECURITY.md](SECURITY.md)
- **API 문서**: http://localhost:8001/docs

---

**BTCUSDT Futures 자동매매 시스템 설정 완료!** 🎉

이제 TradingView에서 시그널이 발생하면 자동으로 Binance/OKX Futures에 주문이 실행되고, 텔레그램으로 실시간 알림을 받을 수 있습니다! 🚀
