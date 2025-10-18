# TradingView Webhook 자동 주문 시스템 완벽 가이드

## 📋 목차

1. [시스템 개요](#시스템-개요)
2. [사전 준비](#사전-준비)
3. [API 키 등록](#api-키-등록)
4. [Pine Script 설정](#pine-script-설정)
5. [TradingView 알림 생성](#tradingview-알림-생성)
6. [보안 설정](#보안-설정)
7. [테스트 및 검증](#테스트-및-검증)
8. [문제 해결](#문제-해결)

---

## 시스템 개요

### 작동 흐름

```
TradingView 차트
    ↓ 시그널 발생
TradingView 알림
    ↓ HTTP POST (Webhook)
우리 백엔드 서버
    ↓ 시그널 검증
Binance/OKX API
    ↓ 주문 실행
실제 거래 체결
```

### 지원 기능

✅ **롱/숏 자동 진입**
- TradingView 시그널 발생 시 자동 주문
- 레버리지 자동 설정
- 포지션 크기 자동 계산

✅ **손절/익절 자동 실행**
- ATR 기반 자동 손절가 설정
- ATR 기반 자동 익절가 설정
- 가격 도달 시 자동 청산

✅ **다중 거래소 지원**
- Binance Futures
- OKX Futures

✅ **보안 검증**
- Webhook Secret 키 검증
- API 키 안전 저장
- IP 제한 가능

---

## 사전 준비

### 1. 거래소 API 키 발급

#### Binance Futures API 키 생성

1. Binance 로그인
2. **프로필 → API Management** 클릭
3. **Create API** 클릭
4. API 이름 입력 (예: "TradingBot AI")
5. ⚠️ **Enable Futures** 반드시 체크
6. 2FA 인증 완료
7. API Key와 Secret Key 복사 (Secret은 한 번만 표시됨!)

**테스트넷 (권장):**
- https://testnet.binancefuture.com
- 무료 테스트 USDT 제공
- 실제 손실 위험 없음

#### OKX Futures API 키 생성

1. OKX 로그인
2. **프로필 → API → Create V5 API Key**
3. API 이름 입력
4. Passphrase 설정 (복구 불가능 - 반드시 기록!)
5. **Trade** 권한 체크
6. 2FA 인증
7. API Key, Secret Key, Passphrase 모두 복사

### 2. 백엔드 서버 실행

```bash
cd trading-backend
python main.py
```

서버가 `http://localhost:8001`에서 실행됩니다.

### 3. Webhook Secret 키 생성

보안을 위해 고유한 Secret 키를 생성하세요:

```python
import secrets
webhook_secret = secrets.token_urlsafe(32)
print(webhook_secret)
# 예: "dQw4w9WgXcQ_r7W3T4z8K9p5L2m6N1v3B"
```

---

## API 키 등록

### Binance 계정 등록

**API 엔드포인트:**
```
POST http://localhost:8001/api/v1/accounts/binance/register
```

**요청 예시:**
```json
{
  "account_id": "my_binance_account",
  "api_key": "YOUR_BINANCE_API_KEY",
  "api_secret": "YOUR_BINANCE_API_SECRET",
  "testnet": true
}
```

**cURL 명령어:**
```bash
curl -X POST http://localhost:8001/api/v1/accounts/binance/register \
  -H "Content-Type: application/json" \
  -d '{
    "account_id": "my_binance_account",
    "api_key": "YOUR_BINANCE_API_KEY",
    "api_secret": "YOUR_BINANCE_API_SECRET",
    "testnet": true
  }'
```

### OKX 계정 등록

**API 엔드포인트:**
```
POST http://localhost:8001/api/v1/accounts/okx/register
```

**요청 예시:**
```json
{
  "account_id": "my_okx_account",
  "api_key": "YOUR_OKX_API_KEY",
  "api_secret": "YOUR_OKX_API_SECRET",
  "passphrase": "YOUR_OKX_PASSPHRASE",
  "testnet": true
}
```

**성공 응답:**
```json
{
  "success": true,
  "message": "Binance account registered successfully",
  "account_id": "my_binance_account",
  "exchange": "binance"
}
```

---

## Pine Script 설정

### 1. 전략 Export

백엔드에서 Pine Script를 생성합니다:

```bash
POST http://localhost:8001/api/v1/simple/export-pine
```

**요청:**
```json
{
  "preset_id": "balanced_trader"
}
```

### 2. Webhook 알림 코드 추가

Pine Script 맨 아래에 다음 코드를 추가:

```pinescript
// ==================== TradingView Webhook 자동 주문 ====================

// 롱 진입 알림
if (longSignal and strategy.position_size == 0)
    alert('{"account_id":"my_binance_account","exchange":"binance","action":"long","symbol":"BTCUSDT","leverage":10,"secret":"YOUR_SECRET_KEY"}', alert.freq_once_per_bar_close)

// 숏 진입 알림
if (shortSignal and strategy.position_size == 0)
    alert('{"account_id":"my_binance_account","exchange":"binance","action":"short","symbol":"BTCUSDT","leverage":10,"secret":"YOUR_SECRET_KEY"}', alert.freq_once_per_bar_close)

// 익절 알림 (롱)
if (strategy.position_size > 0 and ta.cross(close, takeProfit))
    alert('{"account_id":"my_binance_account","exchange":"binance","action":"close_long","symbol":"BTCUSDT","secret":"YOUR_SECRET_KEY"}', alert.freq_once_per_bar_close)

// 익절 알림 (숏)
if (strategy.position_size < 0 and ta.cross(close, takeProfit))
    alert('{"account_id":"my_binance_account","exchange":"binance","action":"close_short","symbol":"BTCUSDT","secret":"YOUR_SECRET_KEY"}', alert.freq_once_per_bar_close)

// 손절 알림 (롱)
if (strategy.position_size > 0 and ta.cross(close, stopLoss))
    alert('{"account_id":"my_binance_account","exchange":"binance","action":"close_long","symbol":"BTCUSDT","secret":"YOUR_SECRET_KEY"}', alert.freq_once_per_bar_close)

// 손절 알림 (숏)
if (strategy.position_size < 0 and ta.cross(close, stopLoss))
    alert('{"account_id":"my_binance_account","exchange":"binance","action":"close_short","symbol":"BTCUSDT","secret":"YOUR_SECRET_KEY"}', alert.freq_once_per_bar_close)
```

⚠️ **반드시 변경해야 할 값:**
- `my_binance_account` → 본인의 account_id
- `YOUR_SECRET_KEY` → 생성한 Secret 키
- `BTCUSDT` → 거래할 심볼
- `10` → 원하는 레버리지

### 3. TradingView에 업로드

1. TradingView Pine Editor 열기
2. 생성된 코드 전체 복사 → 붙여넣기
3. "차트에 추가" 클릭
4. 백테스트 결과 확인

---

## TradingView 알림 생성

### 1. 알림 생성

1. TradingView 차트에서 **알림 아이콘 (⏰)** 클릭
2. **"알림 생성"** 클릭

### 2. 조건 설정

- **조건**: 본인의 전략 이름 선택 (예: "SuperTrend Strategy")
- **옵션**:
  - "Once Per Bar Close" 선택 (권장)
  - "Only Once" 체크 해제

### 3. Webhook 설정

**Webhook URL:**
```
http://localhost:8001/api/v1/webhook/tradingview
```

**메시지 (예시):**
```json
{"account_id":"my_binance_account","exchange":"binance","action":"long","symbol":"BTCUSDT","leverage":10,"secret":"YOUR_SECRET_KEY"}
```

⚠️ **주의:**
- JSON 형식이 정확해야 합니다
- 큰따옴표(") 사용 필수
- 쉼표(,) 위치 확인

### 4. 알림 저장

- 알림 이름 입력 (예: "BTC 자동매매")
- "생성" 클릭

---

## 보안 설정

### 1. Secret 키 관리

**환경변수로 관리 (권장):**

```bash
# .env 파일 생성
WEBHOOK_SECRET=your_generated_secret_key_here
```

**코드 수정:**
```python
# webhook.py
import os
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "default_key")
```

### 2. IP 제한

거래소 API 설정에서 IP 주소를 제한하세요:

**Binance:**
- API Management → Edit API → Restrict access to trusted IPs only
- 백엔드 서버 IP 추가

**OKX:**
- API Management → IP Whitelist
- 백엔드 서버 IP 추가

### 3. API 권한 최소화

- **거래(Trade)** 권한만 부여
- **출금(Withdraw)** 권한 절대 부여하지 말 것
- 읽기 권한은 선택사항

---

## 테스트 및 검증

### 1. 헬스체크

```bash
curl http://localhost:8001/api/v1/webhook/health
```

**응답:**
```json
{
  "status": "healthy",
  "service": "TradingView Webhook Receiver",
  "registered_accounts": {
    "binance": 1,
    "okx": 0
  }
}
```

### 2. 계정 상태 확인

```bash
curl "http://localhost:8001/api/v1/accounts/status/my_binance_account?exchange=binance"
```

**응답:**
```json
{
  "account_id": "my_binance_account",
  "exchange": "binance",
  "balance": {
    "asset": "USDT",
    "available_balance": 10000.0,
    "total_balance": 10000.0
  },
  "positions": [],
  "open_orders": []
}
```

### 3. 수동 Webhook 테스트

```bash
curl -X POST http://localhost:8001/api/v1/webhook/tradingview \
  -H "Content-Type: application/json" \
  -d '{
    "account_id": "my_binance_account",
    "exchange": "binance",
    "action": "long",
    "symbol": "BTCUSDT",
    "leverage": 10,
    "secret": "YOUR_SECRET_KEY"
  }'
```

**성공 응답:**
```json
{
  "success": true,
  "message": "LONG order executed on binance",
  "order_details": {
    "success": true,
    "exchange": "binance",
    "account_id": "my_binance_account",
    "action": "long",
    "symbol": "BTCUSDT",
    "results": {
      "leverage": {...},
      "entry": {...}
    }
  }
}
```

---

## 문제 해결

### 1. 주문이 실행되지 않음

**체크리스트:**
- [ ] 백엔드 서버 실행 중인가?
- [ ] API 키가 올바르게 등록되었나?
- [ ] Webhook Secret이 일치하나?
- [ ] 거래소 계정에 충분한 잔액이 있나?
- [ ] API 키에 Futures 권한이 있나?
- [ ] IP 제한이 설정되어 있다면 서버 IP가 허용되었나?

**디버깅:**
```bash
# 등록된 계정 확인
curl http://localhost:8001/api/v1/accounts/list

# 로그 확인
tail -f logs/app.log
```

### 2. "Invalid webhook secret" 에러

- Pine Script의 `secret` 값 확인
- 환경변수 `WEBHOOK_SECRET` 확인
- 큰따옴표(") 누락 여부 확인

### 3. "Account not found" 에러

- `account_id`가 정확히 일치하는지 확인
- 계정이 제대로 등록되었는지 확인:
  ```bash
  curl http://localhost:8001/api/v1/accounts/list
  ```

### 4. "Insufficient balance" 에러

- 거래소 계정 잔액 확인
- 레버리지 설정 확인
- 최소 주문 수량 확인

### 5. TradingView 알림이 발생하지 않음

- Pine Script 코드의 시그널 조건 확인
- 백테스트에서 시그널이 발생하는지 확인
- `alert.freq_once_per_bar_close` 설정 확인

---

## 고급 설정

### 1. 수량 수동 지정

```json
{
  "account_id": "my_account",
  "exchange": "binance",
  "action": "long",
  "symbol": "BTCUSDT",
  "quantity": 0.01,  // BTC 수량
  "leverage": 10,
  "secret": "YOUR_SECRET"
}
```

### 2. 손절/익절가 수동 지정

```json
{
  "account_id": "my_account",
  "exchange": "binance",
  "action": "long",
  "symbol": "BTCUSDT",
  "leverage": 10,
  "stop_loss": 48000,
  "take_profit": 52000,
  "secret": "YOUR_SECRET"
}
```

### 3. 다중 계정 관리

```python
# 여러 계정 등록
accounts = [
    {"account_id": "account_1", "api_key": "...", "api_secret": "..."},
    {"account_id": "account_2", "api_key": "...", "api_secret": "..."}
]

# Pine Script에서 계정 선택
alert('{"account_id":"account_1",...}', ...)
```

---

## API 레퍼런스

### Webhook Payload 구조

```typescript
interface WebhookPayload {
  account_id: string;      // 필수: 계정 ID
  exchange: "binance" | "okx";  // 필수: 거래소
  action: "long" | "short" | "close_long" | "close_short" | "close_all";  // 필수: 액션
  symbol: string;          // 필수: 심볼 (예: "BTCUSDT")
  price?: number;          // 선택: 현재 가격
  quantity?: number;       // 선택: 수량 (미지정시 계좌의 10%)
  leverage?: number;       // 선택: 레버리지
  stop_loss?: number;      // 선택: 손절가
  take_profit?: number;    // 선택: 익절가
  secret: string;          // 필수: 검증 키
}
```

### 지원 액션

| 액션 | 설명 | 예시 |
|------|------|------|
| `long` | 롱 포지션 진입 | 상승 예상 시 매수 |
| `short` | 숏 포지션 진입 | 하락 예상 시 매도 |
| `close_long` | 롱 포지션 청산 | 롱 포지션 종료 |
| `close_short` | 숏 포지션 청산 | 숏 포지션 종료 |
| `close_all` | 모든 포지션 청산 | 긴급 종료 |

---

## 보안 체크리스트

### 운영 전 필수 확인사항

- [ ] **테스트넷에서 충분히 테스트**
  - 최소 1주일 이상 시뮬레이션
  - 다양한 시나리오 테스트

- [ ] **Secret 키 보안**
  - 환경변수로 관리
  - 코드에 하드코딩 금지
  - GitHub에 절대 업로드 금지

- [ ] **API 키 보안**
  - IP 제한 설정
  - 거래 권한만 부여
  - 정기적으로 키 교체

- [ ] **모니터링 설정**
  - 로그 확인 시스템 구축
  - 이상 거래 알림 설정
  - 일일 손익 확인

- [ ] **리스크 관리**
  - 최대 레버리지 제한
  - 일일 최대 손실 한도 설정
  - 포지션 크기 제한

---

## 자주 묻는 질문 (FAQ)

### Q: 실계좌에서 사용해도 되나요?

A: **테스트넷에서 최소 1-2주 테스트 후** 사용하세요. 처음에는 소액으로 시작하고, 안정성이 검증된 후 금액을 늘리세요.

### Q: 레버리지는 얼마로 설정해야 하나요?

A: 초보자는 **1-3배**, 경험자는 **3-10배**, 전문가는 **10-20배**를 권장합니다. 높은 레버리지는 높은 위험을 의미합니다.

### Q: 수수료는 얼마나 드나요?

A: Binance Futures 기본 수수료는 **0.04%** (Maker/Taker)입니다. OKX도 비슷합니다.

### Q: 인터넷이 끊기면 어떻게 되나요?

A: TradingView 알림은 클라우드에서 발생하므로 괜찮지만, 백엔드 서버가 다운되면 주문이 실행되지 않습니다. **AWS 또는 클라우드 호스팅 권장**.

### Q: 여러 전략을 동시에 실행할 수 있나요?

A: 네, 각 전략마다 다른 `account_id`를 사용하거나, 같은 계정에 여러 알림을 설정할 수 있습니다.

---

## 지원

### 이슈 리포팅

GitHub Issues: https://github.com/your-repo/trading-backend/issues

### 커뮤니티

- Discord: https://discord.gg/your-server
- Telegram: https://t.me/your-group

---

## 라이선스

MIT License

---

**⚠️ 면책 조항:**

이 시스템은 교육 목적으로 제공됩니다. 실제 거래에서 발생하는 손실에 대해 개발자는 책임지지 않습니다. 암호화폐 거래는 높은 위험을 동반하며, 투자 원금 손실 가능성이 있습니다. 본인의 판단과 책임 하에 사용하세요.
