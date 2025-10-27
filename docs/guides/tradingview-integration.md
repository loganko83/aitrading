# TradingView 통합 가이드

TradingView Pine Script를 사용하여 자동매매 알림을 설정하는 방법을 알아보세요.

## 📚 Pine Script란?

**Pine Script**는 TradingView의 프로그래밍 언어로, 커스텀 지표와 전략을 만들 수 있습니다.

## 🚀 기본 템플릿

### SuperTrend 전략 예시

```pinescript
//@version=5
indicator("TradingBot Auto Trade - SuperTrend", overlay=true)

// ========================================
// 설정 (여기를 수정하세요)
// ========================================
API_KEY_ID = "YOUR_API_KEY_ID"  // Settings → API Keys에서 확인
EXCHANGE = "binance"             // binance 또는 okx
SECRET = "YOUR_SECRET_TOKEN"     // Webhooks 페이지에서 확인

// ========================================
// SuperTrend 지표
// ========================================
atrPeriod = input.int(10, "ATR Period", minval=1)
factor = input.float(3.0, "Factor", minval=0.01, step=0.01)

[supertrend, direction] = ta.supertrend(factor, atrPeriod)

// 차트에 표시
plot(supertrend, color=direction < 0 ? color.green : color.red, linewidth=2)
plotshape(direction < 0 and direction[1] >= 0, "Long Entry", shape.triangleup, location.belowbar, color.green, size=size.small)
plotshape(direction > 0 and direction[1] <= 0, "Short Entry", shape.triangledown, location.abovebar, color.red, size=size.small)

// ========================================
// 알림 (Webhook)
// ========================================

// 롱 진입 시그널
if ta.crossover(close, supertrend)
    alert(
        {account_id:' + API_KEY_ID + ', exchange:' + EXCHANGE + ', action:long, symbol:BTCUSDT, secret:' + SECRET + '},
        alert.freq_once_per_bar_close
    )

// 숏 진입 시그널
if ta.crossunder(close, supertrend)
    alert(
        {account_id:' + API_KEY_ID + ', exchange:' + EXCHANGE + ', action:short, symbol:BTCUSDT, secret:' + SECRET + '},
        alert.freq_once_per_bar_close
    )

// 롱 포지션 청산 (숏 시그널 발생 시)
if ta.crossunder(close, supertrend)
    alert(
        {account_id:' + API_KEY_ID + ', exchange:' + EXCHANGE + ', action:close_long, symbol:BTCUSDT, secret:' + SECRET + '},
        alert.freq_once_per_bar_close
    )

// 숏 포지션 청산 (롱 시그널 발생 시)
if ta.crossover(close, supertrend)
    alert(
        {account_id:' + API_KEY_ID + ', exchange:' + EXCHANGE + ', action:close_short, symbol:BTCUSDT, secret:' + SECRET + '},
        alert.freq_once_per_bar_close
    )
```

## 🔧 설정 방법

### 1단계: Pine Editor 열기

```
TradingView → 하단 Pine Editor 클릭
```

### 2단계: 코드 복사

위 템플릿을 Pine Editor에 붙여넣기

### 3단계: 설정 수정

```pinescript
API_KEY_ID = "550e8400-e29b-41d4-a716-446655440000"  // Settings 페이지에서 복사
EXCHANGE = "binance"                                 // binance 또는 okx
SECRET = "yER8UxvSY0klei4vveGAJltJk5uQDYIyYtnU6ctH6cM"  // Webhooks 페이지에서 복사
```

### 4단계: Save 및 차트에 적용

```
1. Save 버튼 클릭
2. 이름 입력: "BTCUSDT Auto Trade"
3. Add to Chart 클릭
```

## 🔔 알림 설정

### 1단계: Create Alert 클릭

```
TradingView 우측 → 알림 아이콘 → Create Alert
```

### 2단계: 알림 조건 설정

```
Condition: BTCUSDT Auto Trade
Options:
  ✅ Once Per Bar Close (중요!)
  Expiration: Open-ended
  
Notifications:
  Webhook URL: https://trendy.storydot.kr/api/v1/webhook/tradingview
  
  ⚠️ Message는 비워두세요 (Pine Script에서 자동 생성)
```

### 3단계: Create 클릭

알림이 활성화되면 **초록색 알림 아이콘**이 차트에 표시됩니다.

## 📊 다양한 전략 예시

### RSI + EMA 전략

```pinescript
//@version=5
indicator("TradingBot - RSI EMA", overlay=true)

API_KEY_ID = "YOUR_API_KEY_ID"
EXCHANGE = "binance"
SECRET = "YOUR_SECRET_TOKEN"

// RSI
rsiLength = input.int(14, "RSI Length")
rsiSource = input(close, "RSI Source")
rsi = ta.rsi(rsiSource, rsiLength)

// EMA
emaLength = input.int(200, "EMA Length")
ema = ta.ema(close, emaLength)

// 차트에 표시
plot(ema, "EMA", color.blue, linewidth=2)
bgcolor(rsi > 70 ? color.new(color.red, 90) : rsi < 30 ? color.new(color.green, 90) : na)

// 롱 진입: RSI 과매도 + 가격 > EMA
longCondition = ta.crossover(rsi, 30) and close > ema
if longCondition
    alert({account_id:' + API_KEY_ID + ', exchange:' + EXCHANGE + ', action:long, symbol:BTCUSDT, secret:' + SECRET + '}, alert.freq_once_per_bar_close)

// 숏 진입: RSI 과매수 + 가격 < EMA
shortCondition = ta.crossunder(rsi, 70) and close < ema
if shortCondition
    alert({account_id:' + API_KEY_ID + ', exchange:' + EXCHANGE + ', action:short, symbol:BTCUSDT, secret:' + SECRET + '}, alert.freq_once_per_bar_close)
```

### EMA Crossover 전략

```pinescript
//@version=5
indicator("TradingBot - EMA Crossover", overlay=true)

API_KEY_ID = "YOUR_API_KEY_ID"
EXCHANGE = "binance"
SECRET = "YOUR_SECRET_TOKEN"

// 빠른/느린 EMA
fastLength = input.int(12, "Fast EMA")
slowLength = input.int(26, "Slow EMA")

fastEma = ta.ema(close, fastLength)
slowEma = ta.ema(close, slowLength)

// 차트에 표시
plot(fastEma, "Fast EMA", color.green, linewidth=2)
plot(slowEma, "Slow EMA", color.red, linewidth=2)

// 골든 크로스 (롱 진입)
if ta.crossover(fastEma, slowEma)
    alert({account_id:' + API_KEY_ID + ', exchange:' + EXCHANGE + ', action:long, symbol:BTCUSDT, secret:' + SECRET + '}, alert.freq_once_per_bar_close)

// 데드 크로스 (숏 진입)
if ta.crossunder(fastEma, slowEma)
    alert({account_id:' + API_KEY_ID + ', exchange:' + EXCHANGE + ', action:short, symbol:BTCUSDT, secret:' + SECRET + '}, alert.freq_once_per_bar_close)
```

## 🎯 다중 심볼 지원

### 여러 암호화폐 동시 거래

```pinescript
//@version=5
indicator("Multi Symbol Auto Trade", overlay=true)

API_KEY_ID = "YOUR_API_KEY_ID"
EXCHANGE = "binance"
SECRET = "YOUR_SECRET_TOKEN"

// 현재 심볼 자동 감지
currentSymbol = syminfo.ticker

// SuperTrend
[supertrend, direction] = ta.supertrend(3, 10)
plot(supertrend, color=direction < 0 ? color.green : color.red)

// 롱 진입
if ta.crossover(close, supertrend)
    // 심볼 자동 입력
    alert({account_id:' + API_KEY_ID + ', exchange:' + EXCHANGE + ', action:long, symbol:' + currentSymbol + ', secret:' + SECRET + '}, alert.freq_once_per_bar_close)

// 숏 진입
if ta.crossunder(close, supertrend)
    alert({account_id:' + API_KEY_ID + ', exchange:' + EXCHANGE + ', action:short, symbol:' + currentSymbol + ', secret:' + SECRET + '}, alert.freq_once_per_bar_close)
```

이 스크립트를 사용하면:
- BTCUSDT 차트: BTCUSDT 거래
- ETHUSDT 차트: ETHUSDT 거래
- 각 차트마다 별도 알림 설정

## ⚠️ 중요 주의사항

### 1. Once Per Bar Close 필수

```
❌ Only Once: 한 번만 실행 (위험!)
❌ Once Per Bar: 매 틱마다 실행 (중복 주문 위험)
✅ Once Per Bar Close: 봉이 완성될 때만 실행 (권장)
```

### 2. Webhook URL 확인

```
✅ 올바른 URL: https://trendy.storydot.kr/api/v1/webhook/tradingview
❌ 틀린 URL: http://localhost:8001/... (로컬 서버 주소)
```

### 3. JSON 형식 검증

```javascript
// ✅ 올바른 JSON
{"account_id":"abc", "exchange":"binance", "action":"long", "symbol":"BTCUSDT", "secret":"xyz"}

// ❌ 틀린 JSON (따옴표 없음)
{account_id:abc, exchange:binance, ...}

// ❌ 틀린 JSON (큰따옴표 대신 작은따옴표)
{account_id:abc, ...}
```

### 4. Secret Token 보안

```
❌ GitHub에 공개 코드로 업로드
❌ 스크린샷에 포함
✅ Pine Script 변수로만 사용
✅ 주기적으로 재생성
```

## 🧪 테스트 방법

### 1. Strategy Tester 사용

```pinescript
//@version=5
strategy("Test Strategy", overlay=true)

// 전략 로직
[supertrend, direction] = ta.supertrend(3, 10)

// 진입/청산
if ta.crossover(close, supertrend)
    strategy.entry("Long", strategy.long)
    
if ta.crossunder(close, supertrend)
    strategy.close("Long")
```

TradingView 하단 → Strategy Tester → 성과 확인

### 2. Paper Trading

```
1. 알림 설정
2. Testnet API Key 사용
3. 실제 시그널 발생 시 동작 확인
4. Dashboard에서 거래 내역 확인
```

## 📚 다음 단계

- [전략 선택 가이드](strategy-selection.md)
- [백테스팅 가이드](../advanced/backtesting.md)
- [파라미터 최적화](../advanced/optimization.md)
