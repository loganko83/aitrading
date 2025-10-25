# TradingBot AI - Claude Code 프로젝트 컨텍스트

이 파일은 TradingBot AI 백엔드 프로젝트의 모든 개발 가이드와 운영 문서를 통합합니다.
다음 작업 시 이 파일을 참조하면 모든 시스템 정보를 자동으로 활용할 수 있습니다.

---

## 📚 핵심 문서 참조

필요한 가이드 문서를 참조하여 정보를 확인할 수 있습니다.

### 🚀 시작 가이드
- [README.md](README.md)
- [BTCUSDT_QUICKSTART.md](BTCUSDT_QUICKSTART.md)

### 🤖 AI 및 전략 관리
- [PINE_SCRIPT_GUIDE.md](PINE_SCRIPT_GUIDE.md)

### 📱 알림 및 통합
- [TELEGRAM_SETUP_GUIDE.md](TELEGRAM_SETUP_GUIDE.md)
- [TRADINGVIEW_GUIDE.md](TRADINGVIEW_GUIDE.md)
- [TRADINGVIEW_WEBHOOK_GUIDE.md](TRADINGVIEW_WEBHOOK_GUIDE.md)

### 🔐 보안 및 운영
- [SECURITY.md](SECURITY.md)

### 📖 개발자 가이드
- [USAGE_GUIDE.md](USAGE_GUIDE.md)
- [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)
- [FRONTEND_INTEGRATION.md](FRONTEND_INTEGRATION.md)
- [PERFORMANCE_GUIDE.md](PERFORMANCE_GUIDE.md)
- [OPTIMIZATION_GUIDE.md](OPTIMIZATION_GUIDE.md)
- [SYSTEM_COMPLETE.md](SYSTEM_COMPLETE.md)

---

## 🎯 프로젝트 개요

### 시스템 아키텍처
```
TradingView (Pine Script)
        ↓ Webhook
  Backend (FastAPI)
        ↓
  ├─→ Binance Futures
  ├─→ OKX Futures
  └─→ Telegram 알림
```

### 핵심 기능
1. **TradingView Webhook 통합**: Pine Script → 자동 주문 실행
2. **Triple AI Ensemble**: ML + GPT-4 + Llama 3 분석
3. **Pine Script 라이브러리**: 5개 검증된 전략 템플릿
4. **AI 기반 전략 생성**: 자연어 → Pine Script 자동 생성
5. **텔레그램 실시간 알림**: 주문, 손익, 에러 즉시 알림
6. **다중 거래소 지원**: Binance Futures, OKX Futures

### 기술 스택
- **Backend**: FastAPI, Python 3.10+
- **Database**: PostgreSQL, Redis
- **AI**: OpenAI GPT-4, Anthropic Claude, Local Llama
- **Exchange APIs**: Binance Futures, OKX Futures
- **Notifications**: Telegram Bot API
- **Analysis**: Pine Script Analyzer, Strategy Optimizer

---

## 📁 프로젝트 구조

```
trading-backend/
├── app/
│   ├── api/v1/
│   │   ├── webhook.py              # TradingView 웹훅
│   │   ├── telegram.py             # 텔레그램 알림
│   │   ├── pine_script.py          # Pine Script 생성/분석
│   │   ├── accounts.py             # 계정 관리
│   │   ├── trading.py              # 주문 실행
│   │   ├── strategies.py           # 전략 관리
│   │   └── backtest.py             # 백테스팅
│   ├── core/
│   │   ├── config.py               # 환경 설정
│   │   ├── exceptions.py           # 예외 처리
│   │   ├── logging_config.py       # 로깅 시스템
│   │   └── cache.py                # 캐싱 시스템
│   ├── services/
│   │   ├── order_executor.py       # 주문 실행 엔진
│   │   ├── telegram_service.py     # 텔레그램 서비스
│   │   ├── pine_script_analyzer.py # Pine Script 분석기
│   │   ├── strategy_optimizer.py   # 전략 최적화
│   │   └── ai_ensemble.py          # Triple AI Ensemble
│   └── models/
│       ├── api_key.py              # API 키 모델
│       └── strategy.py             # 전략 모델
├── alembic/                        # Database Migrations
├── logs/                           # 로그 파일
├── pine_scripts/                   # Pine Script 템플릿
└── *.md                            # 문서 파일들
```

---

## 🔑 주요 API 엔드포인트

### Webhook & Trading
- `POST /api/v1/webhook/tradingview` - TradingView 시그널 수신
- `POST /api/v1/accounts/register` - 거래소 API 키 등록

### Telegram
- `POST /api/v1/telegram/register` - 텔레그램 채팅 ID 등록
- `POST /api/v1/telegram/test` - 테스트 알림 전송

### Pine Script (AI)
- `GET /api/v1/pine-script/strategies` - 전략 라이브러리 조회
- `POST /api/v1/pine-script/customize` - 전략 커스터마이징
- `POST /api/v1/pine-script/analyze` - Pine Script 분석 (AI)
- `POST /api/v1/pine-script/generate` - 전략 생성 (AI)

---

## 🔧 환경 설정

### 필수 환경변수 (.env)

```env
# Application
DEBUG=True
ENVIRONMENT=development

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/tradingbot

# Binance Futures
BINANCE_API_KEY=your_testnet_api_key
BINANCE_API_SECRET=your_testnet_api_secret
BINANCE_TESTNET=True

# AI APIs
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Security
SECRET_KEY=generate-with-openssl-rand-hex-32
WEBHOOK_SECRET=generate-with-python-secrets
ENCRYPTION_KEY=generate-with-fernet

# Telegram
TELEGRAM_BOT_TOKEN=123456789:ABC...

# Trading Parameters
DEFAULT_LEVERAGE=3
MAX_POSITION_SIZE_PCT=0.10
```

---

## 🚀 빠른 시작

### 로컬 개발 환경 (Windows)
```bash
cd C:\dev\trading\trading-backend
python main.py
# http://localhost:8001
```

### AWS 운영 서버 (trendy.storydot.kr)

**서버 접속**:
```bash
ssh -i "C:\server\firstkeypair.pem" ubuntu@13.239.192.158
```

**프로젝트 위치**: `/mnt/storage/trading/`

**서비스 관리**:
```bash
# 백엔드 (FastAPI + Gunicorn)
sudo systemctl status trading-backend
sudo systemctl restart trading-backend
sudo systemctl stop trading-backend

# 프론트엔드 (Next.js + PM2)
pm2 list
pm2 restart trading-frontend
pm2 stop trading-frontend
pm2 logs trading-frontend

# 로그 확인
tail -f /mnt/storage/trading/trading-backend/logs/error.log
pm2 logs trading-frontend --lines 50
```

**URL**:
- 프론트엔드: https://trendy.storydot.kr/trading/
- 백엔드 API: https://trendy.storydot.kr/api/v1/
- Swagger: https://trendy.storydot.kr/docs

### 2. API 문서 확인
```
Swagger UI: http://localhost:8001/docs (로컬)
Swagger UI: https://trendy.storydot.kr/docs (운영)
ReDoc: http://localhost:8001/redoc
```

### 3. 핵심 워크플로우

#### BTCUSDT 자동매매 설정 (5분)
1. API 키 등록 → `/api/v1/accounts/register`
2. 전략 선택 → `/api/v1/pine-script/strategies`
3. 전략 커스터마이징 → `/api/v1/pine-script/customize`
4. TradingView에 Pine Script 적용
5. 알림 생성 (Webhook URL 설정)

#### 텔레그램 알림 설정 (3분)
1. @BotFather에서 봇 생성
2. 봇 토큰을 .env에 추가
3. 채팅 ID 등록 → `/api/v1/telegram/register`
4. 테스트 알림 전송 → `/api/v1/telegram/test`

---

## 📊 Pine Script 전략 라이브러리

### 5개 검증된 전략

| ID | 이름 | 난이도 | 승률 | 수익률 | 인기도 |
|----|------|--------|------|--------|--------|
| `ema_crossover` | EMA 크로스오버 | 초보자 | 58.3% | 1.42 | 95 |
| `rsi_reversal` | RSI 평균 회귀 | 초보자 | 62.1% | 1.58 | 90 |
| `macd_rsi_combo` | MACD + RSI | 중급 | 64.5% | 1.72 | 87 |
| `bb_breakout` | 볼린저 밴드 | 중급 | 55.8% | 1.38 | 82 |
| `supertrend` | SuperTrend | 고급 | 60.2% | 1.65 | 78 |

---

## 🔐 보안 체크리스트

### 개발 환경
- [x] Testnet 사용
- [x] DEBUG=True
- [x] 낮은 레버리지 (1-3x)
- [x] 소액 테스트

### 프로덕션 환경
- [ ] DEBUG=False
- [ ] BINANCE_TESTNET=False
- [ ] 강력한 SECRET_KEY 생성
- [ ] HTTPS 설정
- [ ] Rate Limiting 활성화
- [ ] IP 화이트리스트 설정

---

## 📝 개발 히스토리

### v1.0.0 - 기본 시스템
- TradingView Webhook 통합
- Binance/OKX Futures 지원
- Triple AI Ensemble

### v1.1.0 - 보안 강화
- AES-256 API 키 암호화
- Pydantic 입력 검증
- 구조화된 JSON 로깅
- 환경별 설정 분리

### v1.2.0 - 텔레그램 알림
- 실시간 주문 알림
- 손익 업데이트
- 에러 알림
- 스마트 무음 알림

### v1.3.0 - Pine Script AI 시스템 (최신)
- 5개 검증된 전략 라이브러리
- AI 기반 Pine Script 분석 (GPT-4 + Claude)
- AI 기반 전략 생성
- 파라미터 최적화
- Webhook 자동 통합

---

## 🎯 다음 작업 시 참고사항

### 코드 스타일
- Python 3.10+ type hints 사용
- FastAPI async/await 패턴
- Pydantic models for validation
- Structured logging with JSON

### 아키텍처 원칙
- Single Responsibility Principle
- Dependency Injection
- Error handling with custom exceptions
- Service layer pattern

### 테스팅 전략
- Testnet 우선 테스트
- 백테스팅 필수 (최소 6개월)
- 실시간 테스트 (최소 1주일)
- 손절매 설정 확인

### 문서화 규칙
- API docstrings (FastAPI 자동 생성)
- 한글 주석 (비즈니스 로직)
- 영문 주석 (기술적 세부사항)
- README 업데이트 필수

---

## 🔗 외부 리소스

### API 문서
- Binance Futures API: https://binance-docs.github.io/apidocs/futures/en/
- OKX API: https://www.okx.com/docs-v5/en/
- Telegram Bot API: https://core.telegram.org/bots/api
- OpenAI API: https://platform.openai.com/docs/api-reference
- Anthropic API: https://docs.anthropic.com/claude/reference

### TradingView
- Pine Script v5 Reference: https://www.tradingview.com/pine-script-reference/v5/
- Webhooks Guide: https://www.tradingview.com/support/solutions/43000529348

### 추가 자료
- FastAPI Documentation: https://fastapi.tiangolo.com/
- Pydantic V2: https://docs.pydantic.dev/latest/
- SQLAlchemy 2.0: https://docs.sqlalchemy.org/

---

## 📞 지원 및 이슈

### 로그 확인
```bash
# 전체 로그
tail -f logs/app.log

# 에러만
tail -f logs/error.log

# 보안 이벤트
tail -f logs/security.log
```

### 일반적인 문제
1. **"Telegram bot not configured"**: .env에 TELEGRAM_BOT_TOKEN 설정
2. **"Invalid webhook secret"**: WEBHOOK_SECRET 일치 확인
3. **"Account not found"**: API 키 등록 확인
4. **"Database connection error"**: PostgreSQL 실행 확인

---

## 🎉 프로젝트 상태

**현재 버전**: v1.3.0
**상태**: 완전 가동 ✅
**마지막 업데이트**: 2025-01-18

**주요 달성**:
- ✅ TradingView → Binance/OKX 자동매매
- ✅ 텔레그램 실시간 알림
- ✅ 5개 검증된 전략 라이브러리
- ✅ AI 기반 Pine Script 분석/생성
- ✅ 완전한 문서화 (13개 가이드)

**다음 계획**:
- [ ] 프론트엔드 UI 개발 (Next.js)
- [ ] 실시간 성과 대시보드
- [ ] 더 많은 전략 추가 (10개 목표)
- [ ] 백테스팅 자동화
- [ ] 포트폴리오 관리 기능

---

**이 파일을 참조하면 모든 시스템 정보가 자동으로 로드됩니다!** 🚀
