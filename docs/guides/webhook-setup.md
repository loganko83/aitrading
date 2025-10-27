# Webhook 설정 가이드

TradingView 알림을 받아 자동으로 거래를 실행하는 Webhook을 설정하는 방법을 알아보세요.

## 📚 Webhook이란?

**Webhook**은 TradingView에서 보낸 알림을 받아 자동으로 거래를 실행하는 시스템입니다.

```
TradingView 알림 발생
    ↓
Webhook POST 요청
    ↓
TradingBot AI 수신
    ↓
Trading Config 조회
    ↓
주문 크기 자동 계산
    ↓
Binance/OKX API 호출
    ↓
실제 거래 체결 ✅
```

## 🔐 보안 시스템

### Secret Token

모든 Webhook은 고유한 `secret_token`을 가집니다:

- **32자리 랜덤 문자열** (예: `yER8UxvSY0klei4vveGAJltJk5uQDYIyYtnU6ctH6cM`)
- **HMAC-SHA256 서명 검증**으로 위조 방지
- Token이 일치하지 않으면 **401 Unauthorized** 에러

⚠️ **Secret Token을 절대 공개하지 마세요!**

## 🚀 Webhook 생성하기

### 1단계: Webhook 페이지 접속

```
Dashboard → 좌측 메뉴 → Webhooks
```

### 2단계: Create Webhook 클릭

```
Name: BTCUSDT Auto Trade
Description: 비트코인 자동매매 (선택사항)
```

### 3단계: 생성 결과 확인

생성 성공 시 다음 정보가 표시됩니다:

```json
{
  "id": "abc123-def456-ghi789",
  "name": "BTCUSDT Auto Trade",
  "webhook_url": "https://trendy.storydot.kr/api/v1/webhook/tradingview",
  "secret_token": "yER8UxvSY0klei4vveGAJltJk5uQDYIyYtnU6ctH6cM",
  "is_active": true,
  "total_triggers": 0,
  "created_at": "2025-01-01T00:00:00Z"
}
```

**⭐ secret_token을 안전한 곳에 복사하세요!**

## 📨 Webhook 페이로드 구조

TradingView에서 보내는 JSON 형식:

```json
{
  "account_id": "YOUR_API_KEY_ID",
  "exchange": "binance",
  "action": "long",
  "symbol": "BTCUSDT",
  "secret": "YOUR_SECRET_TOKEN"
}
```

### 필수 파라미터

| 파라미터 | 설명 | 예시 |
|---------|------|------|
| `account_id` | API Key ID | `550e8400-e29b-41d4-a716-446655440000` |
| `exchange` | 거래소 | `binance` 또는 `okx` |
| `action` | 액션 | `long`, `short`, `close_long`, `close_short`, `close_all` |
| `symbol` | 심볼 | `BTCUSDT`, `ETHUSDT` |
| `secret` | Secret Token | `yER8UxvSY0klei4vveGAJltJk5uQDYIyYtnU6ctH6cM` |

### 선택 파라미터 (Trading Config에서 자동 계산)

| 파라미터 | 설명 | 비고 |
|---------|------|------|
| `quantity` | 주문 수량 | Trading Config의 investment_value 기준 자동 계산 |
| `leverage` | 레버리지 | Trading Config 설정값 사용 |
| `stop_loss` | 손절가 | Trading Config의 stop_loss_percentage 기준 자동 계산 |
| `take_profit` | 익절가 | Trading Config의 take_profit_percentage 기준 자동 계산 |

## 🎯 액션 타입 상세

### 1. LONG (롱 진입)

```json
{"action": "long", "symbol": "BTCUSDT"}
```

**동작**:
1. 현재 가격으로 롱 포지션 진입
2. Trading Config 기준으로 수량 계산
3. 레버리지 설정
4. Stop Loss / Take Profit 자동 설정

### 2. SHORT (숏 진입)

```json
{"action": "short", "symbol": "ETHUSDT"}
```

**동작**:
1. 현재 가격으로 숏 포지션 진입
2. Trading Config 기준으로 수량 계산
3. 레버리지 설정
4. Stop Loss / Take Profit 자동 설정

### 3. CLOSE_LONG (롱 포지션 청산)

```json
{"action": "close_long", "symbol": "BTCUSDT"}
```

**동작**:
1. BTCUSDT 롱 포지션 전체 청산
2. 시장가로 즉시 청산

### 4. CLOSE_SHORT (숏 포지션 청산)

```json
{"action": "close_short", "symbol": "ETHUSDT"}
```

**동작**:
1. ETHUSDT 숏 포지션 전체 청산
2. 시장가로 즉시 청산

### 5. CLOSE_ALL (모든 포지션 청산)

```json
{"action": "close_all"}
```

**동작**:
1. 모든 심볼의 모든 포지션 청산
2. 긴급 상황에 사용

## 📊 Trading Config 통합

Webhook은 **Trading Config**와 자동으로 연동됩니다:

### 예시

**Trading Config 설정**:
```yaml
API Key: abc-123
Strategy: SuperTrend
Investment Type: percentage
Investment Value: 0.1 (10%)
Leverage: 10x
Stop Loss: 2%
Take Profit: 5%
```

**계좌 잔액**: 1,000 USDT

**Webhook 수신**:
```json
{
  "account_id": "abc-123",
  "action": "long",
  "symbol": "BTCUSDT",
  "secret": "..."
}
```

**자동 계산 결과**:
- 주문 수량: 100 USDT (1,000 USDT × 10%)
- 레버리지: 10배
- 실제 포지션 크기: 1,000 USDT (100 × 10)
- Stop Loss: 현재가 - 2%
- Take Profit: 현재가 + 5%

## 🔍 Webhook 모니터링

### 확인 방법

1. **Webhooks 페이지**:
   - `total_triggers`: 총 실행 횟수
   - `last_triggered`: 마지막 실행 시간

2. **Trades 페이지**:
   - 실제 거래 내역 확인
   - 손익 확인

3. **Dashboard**:
   - 현재 포지션 실시간 확인

## ⚠️ 주의사항

### 1. API Key ID 확인

```
Settings → API Keys에서 등록된 API Key의 ID 확인
❌ 틀린 예: API Key 자체를 입력 (AKIA...)
✅ 올바른 예: API Key ID 입력 (550e8400-e29b...)
```

### 2. Secret Token 보안

```
❌ GitHub 코드에 하드코딩
❌ 스크린샷에 포함하여 공유
❌ 공개 포럼에 질문 시 노출
✅ 환경 변수로 관리
✅ TradingView Pine Script에만 사용
```

### 3. Testnet 먼저 테스트

```
1. Testnet API Key 등록
2. Webhook 생성
3. TradingView 알림 테스트
4. 최소 1주일 테스트
5. 성과 검토 후 실전 투입
```

## 🛠️ 문제 해결

### "Invalid webhook secret" 에러

**원인**: Secret Token 불일치

**해결**:
1. Webhooks 페이지에서 secret_token 확인
2. TradingView Pine Script의 SECRET 변수 수정
3. 알림 다시 설정

### "No active Trading Config found" 에러

**원인**: Trading Config가 비활성화되었거나 없음

**해결**:
1. Settings → Trading Config 확인
2. API Key에 연결된 Config가 있는지 확인
3. is_active가 true인지 확인

### "User not found" 에러

**원인**: API Key ID가 잘못됨

**해결**:
1. Settings → API Keys에서 올바른 ID 복사
2. TradingView Pine Script의 API_KEY_ID 수정

## 📚 다음 단계

- [TradingView 통합 가이드](tradingview-integration.md)
- [Trading Config 설정](trading-config.md)
- [전략 선택 가이드](strategy-selection.md)
