# 📱 텔레그램 알림 설정 가이드

TradingBot AI의 실시간 주문 알림을 텔레그램으로 받는 방법을 설명합니다.

---

## 🤖 1단계: 텔레그램 봇 생성 (5분)

### 1.1 BotFather로 봇 생성

1. 텔레그램 앱에서 **@BotFather** 검색 및 시작
2. `/newbot` 명령어 입력
3. 봇 이름 입력 (예: `TradingBot AI Alerts`)
4. 봇 사용자명 입력 (예: `my_tradingbot_alerts_bot`)
   - 반드시 `bot`으로 끝나야 함
5. **봇 토큰** 복사 (예: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

### 1.2 봇 토큰 환경변수 설정

```bash
# .env 파일에 추가
TELEGRAM_BOT_TOKEN="123456789:ABCdefGHIjklMNOpqrsTUVwxyz"
```

### 1.3 백엔드 재시작

```bash
# 백엔드 재시작하여 새 설정 적용
python main.py
```

---

## 📲 2단계: 채팅 ID 등록 (3분)

### 2.1 봇과 대화 시작

1. 텔레그램에서 생성한 봇 검색 (예: `@my_tradingbot_alerts_bot`)
2. **`/start`** 명령어 전송 (필수!)
   - 봇이 사용자에게 메시지를 보낼 수 있도록 권한 부여

### 2.2 채팅 ID 확인

**방법 1: @userinfobot 사용 (가장 쉬움)**
1. 텔레그램에서 **@userinfobot** 검색
2. `/start` 명령어 전송
3. 봇이 보여주는 **ID** 복사 (예: `123456789`)

**방법 2: API로 직접 확인**
```bash
curl https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates

# 응답 예시:
{
  "ok": true,
  "result": [{
    "message": {
      "from": {
        "id": 123456789,  # <- 이 값이 채팅 ID
        "first_name": "Your Name"
      }
    }
  }]
}
```

### 2.3 백엔드에 채팅 ID 등록

**방법 A: API 호출 (curl)**
```bash
curl -X POST http://localhost:8001/api/v1/telegram/register \
  -H "Content-Type: application/json" \
  -d '{
    "account_id": "my_binance_account",
    "telegram_chat_id": "123456789"
  }'

# 성공 응답:
{
  "account_id": "my_binance_account",
  "telegram_chat_id": "123456789",
  "is_active": true
}
```

**방법 B: Swagger UI 사용**
1. http://localhost:8001/docs 접속
2. **Telegram Notifications** 섹션 → **POST /api/v1/telegram/register** 클릭
3. `account_id`와 `telegram_chat_id` 입력
4. "Try it out" 클릭

---

## ✅ 3단계: 테스트 알림 전송 (1분)

### 3.1 테스트 알림 API 호출

```bash
curl -X POST http://localhost:8001/api/v1/telegram/test \
  -H "Content-Type: application/json" \
  -d '{
    "account_id": "my_binance_account"
  }'
```

### 3.2 텔레그램 확인

텔레그램 봇에서 다음과 같은 테스트 메시지를 받아야 합니다:

```
🚀 롱 진입!

📍 거래소: BINANCE
💰 심볼: BTCUSDT
💵 가격: $67,500.00
📊 수량: 0.01 BTC
⚡ 레버리지: 3x
🔖 주문 ID: TEST_ORDER_123

🕒 시간: 2025-01-18 00:00:00 UTC
```

---

## 🔔 알림 종류

### 1. Webhook 수신 알림

TradingView에서 시그널이 전송되면 즉시 알림:

```
📡 TradingView 시그널 수신

📍 거래소: BINANCE
📊 액션: LONG
💰 심볼: BTCUSDT
📌 상태: ✅ 성공

🕒 2025-01-18 00:00:00 UTC
```

### 2. 주문 실행 알림

실제 주문이 실행되면 상세 알림:

```
🚀 롱 진입!

📍 거래소: BINANCE
💰 심볼: BTCUSDT
💵 가격: $67,500.00
📊 수량: 0.01 BTC
⚡ 레버리지: 3x
🔖 주문 ID: 123456789

🕒 2025-01-18 00:00:00 UTC
```

### 3. 포지션 청산 알림

```
✅ 롱 포지션 청산

📍 거래소: BINANCE
💰 심볼: BTCUSDT
💵 가격: $68,000.00

🕒 2025-01-18 00:00:00 UTC
```

### 4. 에러 알림

주문 실행 실패 시 즉시 알림:

```
⚠️ 에러 발생

🔴 유형: 주문 실행 실패
📝 메시지: Insufficient balance

📋 상세 정보:
  • exchange: binance
  • action: long
  • symbol: BTCUSDT

🕒 2025-01-18 00:00:00 UTC
```

---

## 🔧 고급 설정

### 여러 계정에 대한 알림

각 거래소 계정마다 별도로 등록 가능:

```bash
# Binance 계정
curl -X POST http://localhost:8001/api/v1/telegram/register \
  -H "Content-Type: application/json" \
  -d '{
    "account_id": "my_binance_account",
    "telegram_chat_id": "123456789"
  }'

# OKX 계정
curl -X POST http://localhost:8001/api/v1/telegram/register \
  -H "Content-Type: application/json" \
  -d '{
    "account_id": "my_okx_account",
    "telegram_chat_id": "123456789"
  }'
```

### 알림 설정 조회

```bash
curl http://localhost:8001/api/v1/telegram/my_binance_account

# 응답:
{
  "account_id": "my_binance_account",
  "telegram_chat_id": "123456789",
  "is_active": true
}
```

### 알림 설정 삭제

```bash
curl -X DELETE http://localhost:8001/api/v1/telegram/my_binance_account

# 응답:
{
  "success": true,
  "message": "Telegram settings deleted for account: my_binance_account"
}
```

---

## 🆘 문제 해결

### 봇이 메시지를 보내지 못할 때

**증상**: API 호출은 성공하지만 메시지를 받지 못함

**해결책**:
1. 봇과 대화를 시작했는지 확인 (`/start` 필수!)
2. 채팅 ID가 올바른지 확인 (@userinfobot으로 재확인)
3. 봇 토큰이 유효한지 확인:
   ```bash
   curl https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getMe
   ```

### "Telegram bot not configured" 에러

**해결책**:
1. `.env` 파일에 `TELEGRAM_BOT_TOKEN` 설정 확인
2. 백엔드 재시작
3. 로그 확인:
   ```bash
   tail -f logs/app.log | grep telegram
   ```

### "Invalid Telegram chat ID" 에러

**해결책**:
1. 봇과 대화를 먼저 시작 (`/start`)
2. 올바른 채팅 ID 사용 (숫자만)
3. 음수 채팅 ID는 그룹 채팅 (개인 채팅 ID 사용)

---

## 📊 알림 무음 설정

손익 변화가 작을 때는 무음 알림으로 설정됩니다:

- **1% 미만 변화**: 무음 알림 (🔕)
- **1% 이상 변화**: 일반 알림 (🔔)

이 설정은 `telegram_service.py`에서 수정 가능:

```python
# 손익에 따라 무음 알림 설정
disable_notification = abs(pnl_percent) < 1.0  # 1% 미만 변화는 무음
```

---

## 🔐 보안 권고사항

### 봇 토큰 보안

- ✅ 봇 토큰을 **절대** 공개하지 마세요
- ✅ `.env` 파일에만 저장 (버전 관리 제외)
- ✅ 프로덕션과 개발 환경에서 다른 봇 사용

### 채팅 ID 보안

- ✅ 다른 사람에게 채팅 ID 공유하지 않기
- ✅ 의심스러운 메시지를 받으면 봇 토큰 재발급

---

## 📚 관련 API 엔드포인트

### POST /api/v1/telegram/register
텔레그램 채팅 ID 등록

**Request**:
```json
{
  "account_id": "my_binance_account",
  "telegram_chat_id": "123456789"
}
```

**Response**:
```json
{
  "account_id": "my_binance_account",
  "telegram_chat_id": "123456789",
  "is_active": true
}
```

### GET /api/v1/telegram/{account_id}
텔레그램 설정 조회

### DELETE /api/v1/telegram/{account_id}
텔레그램 설정 삭제

### POST /api/v1/telegram/test
테스트 알림 전송

---

## 💡 추천 설정

### 봇 설정 최적화

1. **BotFather 설정**:
   - `/setdescription` - 봇 설명 추가
   - `/setabouttext` - 봇 소개 텍스트
   - `/setuserpic` - 봇 프로필 사진

2. **알림 필터링**:
   - 중요한 알림만 받고 싶다면 코드 수정
   - 특정 심볼만 알림 받기
   - 특정 거래소만 알림 받기

---

**텔레그램 실시간 알림 설정 완료!** 📱✅

이제 TradingView 시그널이 발생하면 즉시 텔레그램으로 알림을 받을 수 있습니다!
