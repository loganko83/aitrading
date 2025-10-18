# 🚀 TradingBot AI - Complete Setup Guide

본 가이드는 **TradingBot AI** 시스템의 완전한 설치 및 설정 과정을 단계별로 안내합니다.

---

## 📋 목차

1. [사전 요구사항](#사전-요구사항)
2. [데이터베이스 설정](#데이터베이스-설정)
3. [Backend 설정](#backend-설정)
4. [Frontend 설정](#frontend-설정)
5. [API 키 발급](#api-키-발급)
6. [테스트 실행](#테스트-실행)
7. [운영 배포](#운영-배포)
8. [문제 해결](#문제-해결)

---

## 1. 사전 요구사항

### 필수 소프트웨어 설치

**Node.js & npm**
```bash
# Node.js 20.x LTS 설치
# https://nodejs.org/

# 설치 확인
node --version  # v20.x.x
npm --version   # v10.x.x
```

**Python 3.10+**
```bash
# Python 3.10+ 설치
# https://www.python.org/downloads/

# 설치 확인
python --version  # Python 3.10.x or higher
```

**PostgreSQL 14+**
```bash
# PostgreSQL 설치
# Windows: https://www.postgresql.org/download/windows/
# macOS: brew install postgresql@14
# Linux: sudo apt install postgresql-14

# 서비스 시작
# Windows: pg_ctl start
# macOS/Linux: sudo service postgresql start
```

**Redis** (선택사항, 캐싱용)
```bash
# Redis 설치
# Windows: https://github.com/microsoftarchive/redis/releases
# macOS: brew install redis
# Linux: sudo apt install redis-server

# 서비스 시작
redis-server
```

---

## 2. 데이터베이스 설정

### PostgreSQL 데이터베이스 생성

```bash
# PostgreSQL 접속
psql -U postgres

# 데이터베이스 생성
CREATE DATABASE tradingbot;

# 사용자 생성 (선택사항)
CREATE USER tradinguser WITH PASSWORD 'your_password_here';

# 권한 부여
GRANT ALL PRIVILEGES ON DATABASE tradingbot TO tradinguser;

# 종료
\q
```

### 데이터베이스 URL 확인

프로덕션 환경:
```
DATABASE_URL=postgresql://tradinguser:your_password_here@localhost:5432/tradingbot
```

테스트 환경 (기본):
```
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/tradingbot
```

---

## 3. Backend 설정

### 1단계: 가상환경 생성

```bash
cd trading-backend

# 가상환경 생성
python -m venv venv

# 가상환경 활성화
# Windows PowerShell
venv\Scripts\Activate.ps1
# Windows CMD
venv\Scripts\activate.bat
# macOS/Linux
source venv/bin/activate
```

### 2단계: 패키지 설치

```bash
# 패키지 설치
pip install -r requirements.txt

# 설치 확인
pip list
```

### 3단계: 환경 변수 설정

```bash
# .env 파일 생성
cp .env.example .env

# .env 파일 편집
# Windows
notepad .env
# macOS/Linux
nano .env
```

**.env 파일 내용:**
```env
# Application
APP_NAME="TradingBot AI Backend"
DEBUG=True
API_V1_PREFIX="/api/v1"

# Database
DATABASE_URL="postgresql://postgres:postgres@localhost:5432/tradingbot"

# Binance API (Testnet keys)
BINANCE_API_KEY="your-binance-testnet-api-key"
BINANCE_API_SECRET="your-binance-testnet-secret-key"
BINANCE_TESTNET=True

# AI APIs
OPENAI_API_KEY="sk-..."  # OpenAI GPT-4
ANTHROPIC_API_KEY="sk-ant-..."  # Anthropic Claude

# Redis
REDIS_URL="redis://localhost:6379"

# Security
SECRET_KEY="your-secret-key-here-min-32-characters"
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Trading Parameters
DEFAULT_LEVERAGE=3
MAX_POSITION_SIZE_PCT=0.10
ATR_PERIOD=14

# AI Ensemble Weights
ML_WEIGHT=0.40
GPT4_WEIGHT=0.25
LLAMA_WEIGHT=0.25
TA_WEIGHT=0.10

# Entry/Exit Thresholds
MIN_PROBABILITY=0.80
MIN_CONFIDENCE=0.70
MIN_AGREEMENT=0.70
```

### 4단계: 데이터베이스 마이그레이션

```bash
# Alembic 초기 마이그레이션 생성
alembic revision --autogenerate -m "Initial migration"

# 마이그레이션 실행
alembic upgrade head

# 마이그레이션 확인
alembic current
```

### 5단계: Backend 서버 실행

```bash
# 개발 모드 실행 (자동 재시작)
python main.py

# 또는 Uvicorn 직접 실행
uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

**Backend 접속 확인:**
- API: http://localhost:8001
- API Docs: http://localhost:8001/docs
- ReDoc: http://localhost:8001/redoc

---

## 4. Frontend 설정

### 1단계: 패키지 설치

```bash
cd trading-frontend

# 패키지 설치
npm install
```

### 2단계: 환경 변수 설정

```bash
# .env.local 파일 생성
cp .env.example .env.local

# 편집
# Windows
notepad .env.local
# macOS/Linux
nano .env.local
```

**.env.local 파일 내용:**
```env
# Database
DATABASE_URL="postgresql://postgres:postgres@localhost:5432/tradingbot"

# NextAuth
NEXTAUTH_SECRET="your-nextauth-secret-key-min-32-characters"
NEXTAUTH_URL="http://localhost:3000"

# Backend API
NEXT_PUBLIC_API_URL="http://localhost:8001"
NEXT_PUBLIC_WS_URL="ws://localhost:8001"
```

### 3단계: Prisma 설정

```bash
# Prisma 클라이언트 생성
npx prisma generate

# 데이터베이스 마이그레이션
npx prisma migrate dev

# 기본 전략 시드 데이터 추가
npx prisma db seed
```

### 4단계: Frontend 서버 실행

```bash
# 개발 모드 실행
npm run dev

# 또는 Turbopack 사용 (더 빠름)
npm run dev --turbo
```

**Frontend 접속 확인:**
- Web App: http://localhost:3000

---

## 5. API 키 발급

### Binance API 키 (Testnet)

1. **Binance Testnet 가입**
   - https://testnet.binance.vision/

2. **API 키 생성**
   - 로그인 → API Keys → Create API Key
   - API Key와 Secret Key 복사
   - `.env` 파일에 추가

3. **권한 설정**
   - ✅ Enable Trading
   - ✅ Enable Futures
   - ❌ Enable Withdrawals (비활성화 권장)

### OpenAI API 키

1. **OpenAI 계정 생성**
   - https://platform.openai.com/signup

2. **API 키 발급**
   - API Keys → Create new secret key
   - 키 복사 → `.env` 파일에 추가

3. **크레딧 충전**
   - Billing → Add payment method
   - 최소 $5 충전 권장

### Anthropic API 키

1. **Anthropic 계정 생성**
   - https://console.anthropic.com/

2. **API 키 발급**
   - API Keys → Create Key
   - 키 복사 → `.env` 파일에 추가

3. **크레딧 충전**
   - Billing → Add payment method

---

## 6. 테스트 실행

### Backend API 테스트

```bash
# 건강 체크
curl http://localhost:8001/health

# 계좌 잔고 조회
curl http://localhost:8001/api/v1/trading/balance

# AI 분석 테스트
curl -X POST http://localhost:8001/api/v1/trading/analyze \
  -H "Content-Type: application/json" \
  -d '{"symbol": "BTCUSDT", "interval": "1h", "limit": 500}'
```

### Frontend 기능 테스트

1. **회원가입 및 로그인**
   - http://localhost:3000/signup
   - OTP 인증 테스트

2. **대시보드 접속**
   - http://localhost:3000/dashboard
   - 실시간 차트 확인

3. **API 키 설정**
   - Settings → API Keys
   - Binance API 키 등록 및 검증

4. **전략 설정**
   - Strategies → Create New Strategy
   - 백테스팅 실행

5. **자동 거래 활성화**
   - Auto-Trade → Start
   - 실시간 포지션 모니터링

---

## 7. 마진 관리 및 리스크 분석

### Binance Futures 마진 계산

TradingBot AI는 Binance 공식 마진 계산 시스템을 완벽하게 구현했습니다.

#### 초기 증거금 (Initial Margin)

**공식:** `IM = (포지션 크기 × 시장 가격) / 레버리지`

```python
# 예시: 1 BTC @ $65,000, 10x 레버리지
# Initial Margin = (1 × 65,000) / 10 = $6,500 USDT
```

#### 유지 증거금 (Maintenance Margin)

**Binance 레버리지 티어 시스템:**

| 포지션 가치 (USDT) | 최대 레버리지 | 유지 증거금율 |
|-------------------|--------------|--------------|
| 0 - 50,000 | 125x | 0.40% |
| 50,000 - 250,000 | 100x | 0.50% |
| 250,000 - 1,000,000 | 50x | 1.00% |
| 1,000,000 - 10,000,000 | 20x | 2.50% |
| 10,000,000+ | 10x | 5.00% |

#### 청산 가격 계산

**롱 포지션:**
```
청산 가격 = 진입 가격 × (1 - IMR + MMR)
```

**숏 포지션:**
```
청산 가격 = 진입 가격 × (1 + IMR - MMR)
```

### API를 통한 마진 계산 테스트

```bash
# 포지션 마진 계산
curl -X POST http://localhost:8001/api/v1/trading/calculate-margin \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "BTCUSDT",
    "position_size": 0.5,
    "leverage": 10
  }'

# 응답 예시:
{
  "symbol": "BTCUSDT",
  "position_size": 0.5,
  "entry_price": 65000.0,
  "leverage": 10,
  "initial_margin": 3250.0,
  "maintenance_margin": 130.0,
  "maintenance_margin_rate": 0.004,
  "wallet_balance": 10000.0,
  "sufficient_balance": true
}
```

```bash
# 포지션 리스크 분석
curl http://localhost:8001/api/v1/trading/position-risk/BTCUSDT

# 응답 예시:
{
  "symbol": "BTCUSDT",
  "side": "LONG",
  "quantity": 0.5,
  "entry_price": 65000.0,
  "mark_price": 66000.0,
  "leverage": 10,
  "position_value": 33000.0,
  "initial_margin": 3300.0,
  "maintenance_margin": 132.0,
  "margin_balance": 10500.0,
  "margin_ratio": 1.26,
  "unrealized_pnl": 500.0,
  "liquidation_price": 59150.0,
  "risk_level": "SAFE",
  "distance_to_liquidation_pct": 10.38
}
```

```bash
# 안전한 포지션 크기 계산
curl -X POST http://localhost:8001/api/v1/trading/safe-position-size \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "BTCUSDT",
    "leverage": 10,
    "max_risk_pct": 0.10
  }'

# 응답 예시:
{
  "symbol": "BTCUSDT",
  "current_price": 65000.0,
  "available_balance": 10000.0,
  "max_position_size": 0.1538,
  "max_position_value": 10000.0,
  "leverage": 10,
  "max_risk_pct": 0.10,
  "initial_margin": 1000.0,
  "maintenance_margin": 40.0,
  "maintenance_margin_rate": 0.004
}
```

### 리스크 레벨 기준

- **SAFE** (0-30%): 안전한 포지션, 청산 위험 낮음
- **MEDIUM** (30-50%): 보통, 시장 변동성 모니터링 필요
- **HIGH** (50-80%): 위험, 손절매 검토 필요
- **CRITICAL** (80%+): 매우 위험, 즉시 포지션 축소 권장

### 마진 관리 모범 사례

1. **초기 레버리지 제한**
   ```env
   DEFAULT_LEVERAGE=3  # 초보자는 1-3x 권장
   ```

2. **포지션 크기 제한**
   ```env
   MAX_POSITION_SIZE_PCT=0.10  # 계좌의 10% 이내
   ```

3. **마진 비율 모니터링**
   - 30% 이하: 안전
   - 50% 이상: 경고
   - 80% 이상: 청산 임박

4. **손절매 필수 설정**
   ```python
   # ATR 기반 자동 손절매
   stop_loss = entry_price - (atr * leverage * 0.5)
   ```

---

## 8. 운영 배포

### Backend 배포 (Docker)

```bash
# Dockerfile 생성 (예시)
FROM python:3.10-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
```

```bash
# Docker 빌드 및 실행
docker build -t tradingbot-backend .
docker run -d -p 8001:8001 --env-file .env tradingbot-backend
```

### Frontend 배포 (Vercel)

```bash
# Vercel CLI 설치
npm install -g vercel

# 로그인
vercel login

# 배포
vercel --prod
```

---

## 8. 문제 해결

### Backend 실행 오류

**문제: "ModuleNotFoundError: No module named 'X'"**
```bash
# 해결: 패키지 재설치
pip install -r requirements.txt
```

**문제: "Database connection failed"**
```bash
# 해결: PostgreSQL 서비스 확인
sudo service postgresql status  # Linux
pg_ctl status  # Windows

# 데이터베이스 URL 확인
echo $DATABASE_URL  # Linux/macOS
echo %DATABASE_URL%  # Windows
```

**문제: "Binance API key invalid"**
```bash
# 해결: API 키 재확인
# 1. Testnet 키인지 확인
# 2. 권한 설정 확인 (Trading, Futures 활성화)
# 3. IP 제한 설정 확인
```

### Frontend 실행 오류

**문제: "Module not found"**
```bash
# 해결: node_modules 재설치
rm -rf node_modules package-lock.json
npm install
```

**문제: "Prisma Client error"**
```bash
# 해결: Prisma 재생성
npx prisma generate
npx prisma migrate dev
```

**문제: "API connection failed"**
```bash
# 해결: Backend 서버 확인
curl http://localhost:8001/health

# CORS 설정 확인 (main.py)
```

---

## ⚠️ 보안 주의사항

1. **API 키 관리**
   - ❌ `.env` 파일을 Git에 커밋하지 마세요
   - ✅ `.env.example` 템플릿만 공유하세요
   - ✅ 프로덕션과 개발 환경의 키를 분리하세요

2. **데이터베이스 암호**
   - ✅ 강력한 비밀번호 사용 (최소 16자)
   - ✅ 정기적으로 비밀번호 변경

3. **Testnet 사용**
   - ✅ 초기 테스트는 반드시 Testnet에서
   - ✅ 실전 투자 전 충분한 백테스팅

4. **접근 제한**
   - ✅ Binance API IP 화이트리스트 설정
   - ✅ 출금 권한 비활성화

---

## 📞 지원 및 문의

- **Documentation**: README.md
- **API Docs**: http://localhost:8001/docs
- **GitHub Issues**: [GitHub Repository]

---

**준비 완료! Happy Trading! 🚀**
