# 🤖 TradingBot AI Backend

**AI 기반 자동매매 시스템** - TradingView 웹훅을 통한 Binance/OKX Futures 자동 주문 실행

> **핵심 기능**: TradingView 시그널 수신 → AI 분석 → Binance/OKX 선물 주문 → 텔레그램 실시간 알림

---

## 🌟 주요 특징

### 1. **TradingView 웹훅 통합** 📡
- Pine Script 전략에서 실시간 시그널 수신
- HMAC 서명 검증으로 안전한 웹훅 처리
- Replay Attack 방지 (타임스탬프 검증)

### 2. **Triple AI Ensemble** 🧠
- **ML Model** (40%): LSTM 기반 시계열 예측
- **GPT-4** (25%): OpenAI API를 통한 시장 분석
- **Llama 3** (25%): 로컬 LLM을 통한 독립적 분석
- **Technical Analysis** (10%): RSI, MACD, Bollinger Bands

### 3. **다중 거래소 지원** 🏦
- **Binance Futures**: BTCUSDT 영구 선물
- **OKX Futures**: BTC-USDT-SWAP 영구 스왑
- Testnet 모드 지원 (안전한 테스트)

### 4. **실시간 텔레그램 알림** 📱
- 주문 실행 즉시 알림 (롱/숏/청산)
- 포지션 손익 업데이트 (1% 이상 변화 시)
- Webhook 수신 확인 알림
- 에러 발생 즉시 알림

### 5. **보안 & 안정성** 🔐
- AES-256 (Fernet) API 키 암호화
- Pydantic 기반 입력 검증
- 구조화된 JSON 로깅 (app.log, error.log, security.log)
- 환경별 설정 분리 (.env.development, .env.production)

---

## 🚀 빠른 시작 (5분)

### 1️⃣ 사전 준비

**필수 항목**:
```bash
# Python 3.10+
python --version

# PostgreSQL 설치 및 실행
# Redis 설치 및 실행 (선택사항)
```

**API 키 준비**:
- Binance Futures Testnet API Key ([링크](https://testnet.binancefuture.com))
- OpenAI API Key
- Anthropic API Key (Claude)
- Telegram Bot Token ([가이드](TELEGRAM_SETUP_GUIDE.md))

### 2️⃣ 설치

```bash
# 저장소 클론
git clone <repository-url>
cd trading-backend

# Python 가상환경 생성
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 환경변수 설정
cp .env.example .env
# .env 파일을 열어 API 키 입력
```

### 3️⃣ 데이터베이스 설정

```bash
# PostgreSQL 데이터베이스 생성
createdb tradingbot

# Alembic 마이그레이션 실행
alembic upgrade head
```

### 4️⃣ 서버 실행

```bash
# 개발 서버 실행
python main.py

# 또는 uvicorn 직접 실행
uvicorn main:app --reload --port 8001
```

**서버 접속**: http://localhost:8001
**API 문서**: http://localhost:8001/docs

---

## 📋 BTCUSDT 자동매매 설정

> 자세한 가이드: [BTCUSDT_QUICKSTART.md](BTCUSDT_QUICKSTART.md)

### Step 1: API 키 등록

```bash
# Binance Testnet API 키 등록
curl -X POST http://localhost:8001/api/v1/accounts/register \
  -H "Content-Type: application/json" \
  -d '{
    "account_id": "my_binance_account",
    "exchange": "binance",
    "api_key": "YOUR_BINANCE_API_KEY",
    "api_secret": "YOUR_BINANCE_SECRET",
    "testnet": true
  }'
```

### Step 2: TradingView Pine Script 설정

```pine
//@version=5
strategy("BTCUSDT Webhook Strategy", overlay=true)

// EMA 크로스오버 전략
fastEMA = ta.ema(close, 9)
slowEMA = ta.ema(close, 21)

longCondition = ta.crossover(fastEMA, slowEMA)
shortCondition = ta.crossunder(fastEMA, slowEMA)

// 롱 진입
if (longCondition)
    strategy.entry("Long", strategy.long)
    alert('{"account_id":"my_binance_account","exchange":"binance","action":"long","symbol":"BTCUSDT","leverage":3,"secret":"YOUR_WEBHOOK_SECRET","timestamp":' + str.tostring(timenow / 1000) + '}', alert.freq_once_per_bar_close)

// 숏 진입
if (shortCondition)
    strategy.entry("Short", strategy.short)
    alert('{"account_id":"my_binance_account","exchange":"binance","action":"short","symbol":"BTCUSDT","leverage":3,"secret":"YOUR_WEBHOOK_SECRET","timestamp":' + str.tostring(timenow / 1000) + '}', alert.freq_once_per_bar_close)
```

### Step 3: TradingView 알림 설정

1. TradingView 차트에서 **알림 생성** 클릭
2. **Webhook URL**: `http://your-server:8001/api/v1/webhook/tradingview`
3. **메시지**: Pine Script의 alert() 함수가 자동 전송
4. **확인** 클릭

---

## 📱 텔레그램 알림 설정 (3분)

> 자세한 가이드: [TELEGRAM_SETUP_GUIDE.md](TELEGRAM_SETUP_GUIDE.md)

### 1. 텔레그램 봇 생성

```
1. 텔레그램에서 @BotFather 검색
2. /newbot 명령어 입력
3. 봇 이름 및 사용자명 설정
4. 봇 토큰 복사 (예: 123456789:ABCdefGHIjkl...)
5. .env 파일에 TELEGRAM_BOT_TOKEN 설정
```

### 2. 채팅 ID 등록

```bash
# 채팅 ID 확인 (@userinfobot 사용)
# 텔레그램에서 @userinfobot에게 메시지 전송하여 ID 확인

# API로 등록
curl -X POST http://localhost:8001/api/v1/telegram/register \
  -H "Content-Type: application/json" \
  -d '{
    "account_id": "my_binance_account",
    "telegram_chat_id": "123456789"
  }'
```

### 3. 테스트 알림

```bash
curl -X POST http://localhost:8001/api/v1/telegram/test \
  -H "Content-Type: application/json" \
  -d '{"account_id": "my_binance_account"}'
```

**알림 종류**:
- 🚀 롱/숏 진입 알림
- ✅ 포지션 청산 알림
- 📊 손익 업데이트 (1% 이상 변화)
- 📡 Webhook 수신 확인
- ⚠️ 에러 발생 알림

---

## 📚 API 엔드포인트

### 핵심 API

| 엔드포인트 | 메서드 | 설명 |
|-----------|--------|------|
| `/api/v1/webhook/tradingview` | POST | TradingView 웹훅 수신 |
| `/api/v1/accounts/register` | POST | 거래소 API 키 등록 |
| `/api/v1/telegram/register` | POST | 텔레그램 채팅 ID 등록 |
| `/api/v1/telegram/test` | POST | 텔레그램 테스트 알림 |
| `/api/v1/strategies` | GET | 등록된 전략 목록 |
| `/api/v1/backtest/simple` | POST | 간단한 백테스팅 |

### Swagger 문서

**전체 API 문서**: http://localhost:8001/docs

**ReDoc 문서**: http://localhost:8001/redoc

---

## 🔐 보안 가이드

> 자세한 가이드: [SECURITY.md](SECURITY.md)

### 개발 환경

```bash
# .env.development 사용
ENVIRONMENT=development
DEBUG=True
BINANCE_TESTNET=True
```

### 프로덕션 환경

```bash
# .env.production 사용
ENVIRONMENT=production
DEBUG=False
BINANCE_TESTNET=False

# 필수 보안 설정
# 1. 강력한 시크릿 키 생성
openssl rand -hex 32  # SECRET_KEY
python -c "import secrets; print(secrets.token_urlsafe(32))"  # WEBHOOK_SECRET
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"  # ENCRYPTION_KEY

# 2. API 키 권한 최소화
# 3. IP 화이트리스트 설정
# 4. HTTPS 설정
# 5. Rate Limiting 활성화
```

---

## 📦 프로젝트 구조

```
trading-backend/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── trading.py          # 주문 실행 API
│   │       ├── webhook.py          # TradingView 웹훅
│   │       ├── telegram.py         # 텔레그램 알림 API
│   │       ├── strategies.py       # 전략 관리
│   │       ├── backtest.py         # 백테스팅
│   │       └── accounts.py         # API 키 관리
│   ├── core/
│   │   ├── config.py               # 환경 설정
│   │   ├── exceptions.py           # 커스텀 예외
│   │   └── logging_config.py       # 로깅 설정
│   ├── models/
│   │   ├── api_key.py              # API 키 모델
│   │   └── strategy.py             # 전략 모델
│   ├── services/
│   │   ├── ai_ensemble.py          # Triple AI Ensemble
│   │   ├── order_executor.py       # 주문 실행 서비스
│   │   └── telegram_service.py     # 텔레그램 알림
│   └── utils/
│       └── encryption.py           # AES-256 암호화
├── alembic/
│   └── versions/                   # 데이터베이스 마이그레이션
├── pine_scripts/
│   └── btcusdt_simple_strategy.pine # Pine Script 샘플
├── logs/                           # 로그 파일
├── main.py                         # FastAPI 애플리케이션
├── requirements.txt                # Python 의존성
├── .env.example                    # 환경변수 템플릿
├── BTCUSDT_QUICKSTART.md           # BTCUSDT 빠른 시작
├── TELEGRAM_SETUP_GUIDE.md         # 텔레그램 설정 가이드
└── SECURITY.md                     # 보안 가이드
```

---

## 🛠️ 개발 가이드

### 로컬 개발

```bash
# 개발 환경 실행
ENVIRONMENT=development python main.py

# 로그 확인
tail -f logs/app.log
tail -f logs/error.log
tail -f logs/security.log
```

### 데이터베이스 마이그레이션

```bash
# 새 마이그레이션 생성
alembic revision --autogenerate -m "설명"

# 마이그레이션 적용
alembic upgrade head

# 롤백
alembic downgrade -1
```

### 테스트

```bash
# pytest 실행 (추후 추가 예정)
pytest

# 웹훅 테스트
curl -X POST http://localhost:8001/api/v1/webhook/tradingview \
  -H "Content-Type: application/json" \
  -d '{
    "account_id": "my_binance_account",
    "exchange": "binance",
    "action": "long",
    "symbol": "BTCUSDT",
    "leverage": 3,
    "secret": "YOUR_WEBHOOK_SECRET",
    "timestamp": 1704067200
  }'
```

---

## 🚨 문제 해결

### 일반적인 오류

**1. "Telegram bot not configured"**
```bash
# .env 파일에 TELEGRAM_BOT_TOKEN 설정 확인
# 백엔드 재시작
```

**2. "Invalid API key format"**
```bash
# Binance/OKX API 키 형식 확인
# Testnet과 Mainnet API 키 혼용 주의
```

**3. "Webhook secret mismatch"**
```bash
# .env의 WEBHOOK_SECRET과 Pine Script의 secret 값 일치 확인
```

**4. "Database connection error"**
```bash
# PostgreSQL 실행 확인
sudo systemctl status postgresql

# DATABASE_URL 형식 확인
postgresql://user:password@localhost:5432/tradingbot
```

### 로그 확인

```bash
# 전체 애플리케이션 로그
tail -f logs/app.log

# 에러만 확인
tail -f logs/error.log

# 보안 이벤트 확인
tail -f logs/security.log
```

---

## 📈 성능 최적화

### 권장 설정

```env
# .env 파일
DEFAULT_LEVERAGE=3              # 보수적 레버리지
MAX_POSITION_SIZE_PCT=0.10      # 계좌의 10%만 사용
ATR_PERIOD=14                   # ATR 기반 포지션 사이징

# AI Ensemble 가중치
ML_WEIGHT=0.40
GPT4_WEIGHT=0.25
LLAMA_WEIGHT=0.25
TA_WEIGHT=0.10

# 진입/청산 임계값
MIN_PROBABILITY=0.80            # 80% 이상 확률
MIN_CONFIDENCE=0.70             # 70% 이상 신뢰도
MIN_AGREEMENT=0.70              # 70% 이상 AI 합의
```

---

## 🤝 기여 가이드

프로젝트 기여를 환영합니다!

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 라이선스

이 프로젝트는 MIT 라이선스를 따릅니다.

---

## ⚠️ 면책 조항

**이 소프트웨어는 교육 및 연구 목적으로 제공됩니다.**

- 실제 자금을 투자하기 전에 반드시 Testnet에서 충분히 테스트하세요
- 자동매매는 큰 손실을 초래할 수 있습니다
- 본인의 투자 결정에 대한 책임은 본인에게 있습니다
- 개발자는 이 소프트웨어 사용으로 인한 어떠한 손실에도 책임지지 않습니다

**안전한 거래를 위한 권장사항**:
- 처음에는 소액으로 시작
- 레버리지를 낮게 유지 (3x 이하)
- 손절매 설정 필수
- 정기적으로 포지션 모니터링

---

## 📞 지원

**Claude Code 사용자**:
- **@CLAUDE.md** - 모든 프로젝트 문서를 한 번에 참조 (13개 가이드 자동 로드)

**핵심 문서**:
- [BTCUSDT 빠른 시작](BTCUSDT_QUICKSTART.md)
- [Pine Script AI 가이드](PINE_SCRIPT_GUIDE.md)
- [텔레그램 설정 가이드](TELEGRAM_SETUP_GUIDE.md)
- [보안 가이드](SECURITY.md)

**API 문서**:
- Swagger UI: http://localhost:8001/docs
- ReDoc: http://localhost:8001/redoc

**Issues**: GitHub Issues 탭에서 버그 리포트 및 기능 요청

---

**Happy Trading! 🚀📈**
