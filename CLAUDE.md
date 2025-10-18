# TradingBot AI - 개발 가이드 및 시스템 문서

**최종 업데이트**: 2025년 (Session 계속 진행 중)

## 📋 목차

1. [시스템 개요](#시스템-개요)
2. [TradingView Webhook 자동 주문 시스템](#tradingview-webhook-자동-주문-시스템)
3. [보안 시스템 (API 키 암호화)](#보안-시스템)
4. [데이터베이스 구조](#데이터베이스-구조)
5. [API 엔드포인트 가이드](#api-엔드포인트-가이드)
6. [프론트엔드 통합 가이드](#프론트엔드-통합-가이드)
7. [배포 및 운영](#배포-및-운영)

---

## 시스템 개요

### 기술 스택

**Backend:**
- FastAPI (Python 3.10+)
- SQLAlchemy (ORM)
- PostgreSQL (데이터베이스)
- Alembic (마이그레이션)
- Cryptography (AES-256 암호화)

**Frontend:**
- Next.js 14
- NextAuth (인증)
- TypeScript

**거래소 API:**
- Binance Futures API
- OKX Futures API

**외부 서비스:**
- TradingView (Pine Script + Webhook)

### 핵심 기능

1. **AI 기반 트레이딩 전략** (6가지)
   - SuperTrend
   - RSI + EMA
   - MACD + Stochastic
   - Ichimoku Cloud
   - Bollinger Bands + RSI
   - EMA Crossover

2. **백테스팅 엔진**
   - 과거 데이터 기반 성과 분석
   - 승률, 손익, MDD 계산

3. **TradingView 통합**
   - Pine Script 자동 생성
   - Webhook 자동 주문
   - 실시간 시그널 전송

4. **보안 시스템**
   - AES-256 API 키 암호화
   - 사용자별 격리
   - NextAuth 인증

---

## TradingView Webhook 자동 주문 시스템

### 🎯 시스템 작동 흐름

```
1. 사용자 로그인 (NextAuth)
   ↓
2. 설정 페이지에서 API 키 등록
   → POST /api/v1/accounts-secure/register
   → API 키 AES-256 암호화 후 DB 저장
   ↓
3. 전략 선택 및 Pine Script Export
   → GET /api/v1/simple/export-pine
   → Webhook 알림 코드 포함된 Pine Script 생성
   ↓
4. TradingView에 Pine Script 업로드
   → TradingView Pine Editor
   → 차트에 전략 적용
   ↓
5. TradingView 알림 설정
   → Webhook URL: http://your-server:8001/api/v1/webhook/tradingview
   → 메시지: JSON 페이로드
   ↓
6. 시그널 발생 시 자동 주문
   → TradingView → Webhook POST
   → 백엔드 검증 (Secret Key)
   → OrderExecutor → Binance/OKX API
   → 실제 거래 체결
```

### 📁 주요 파일 및 역할

#### 거래소 API 클라이언트
```
app/services/binance_client.py
├─ BinanceClient 클래스
├─ HMAC SHA256 서명 생성
├─ Futures API 메서드
│  ├─ get_account_balance()
│  ├─ get_positions()
│  ├─ set_leverage()
│  ├─ create_market_order()
│  ├─ create_limit_order()
│  ├─ create_stop_loss()
│  ├─ create_take_profit()
│  ├─ close_position()
│  └─ cancel_order()
└─ Retry/Timeout 데코레이터 통합
```

```
app/services/okx_client.py
├─ OKXClient 클래스
├─ Base64 HMAC 서명 (OKX 전용)
├─ Passphrase 지원
├─ 동일한 API 메서드
└─ 심볼 형식: BTC-USDT-SWAP
```

#### 주문 실행 오케스트레이션
```
app/services/order_executor.py
├─ OrderExecutor 클래스
├─ 다중 거래소 계정 관리
├─ execute_signal() - 시그널 → 주문 변환
├─ 자동 포지션 크기 계산 (10% 기본)
├─ ATR 기반 SL/TP 자동 설정
└─ 지원 시그널:
   ├─ LONG - 롱 진입
   ├─ SHORT - 숏 진입
   ├─ CLOSE_LONG - 롱 청산
   ├─ CLOSE_SHORT - 숏 청산
   └─ CLOSE_ALL - 모든 포지션 청산
```

#### Webhook API
```
app/api/v1/webhook.py
├─ POST /webhook/tradingview
│  ├─ TradingView로부터 POST 수신
│  ├─ Secret 키 검증
│  ├─ OrderExecutor 호출
│  └─ 주문 결과 반환
└─ GET /webhook/health - 헬스체크
```

#### Pine Script 생성기
```
app/ai/pine_export.py
├─ PineScriptExporter 클래스
├─ export_strategy() - 전략 → Pine Script 변환
├─ add_webhook_alerts() - Webhook 알림 코드 생성
└─ generate_webhook_setup_guide() - 설정 가이드
```

### 🔧 환경변수 설정

**`.env` 파일 필수 설정:**
```bash
# Webhook 보안
WEBHOOK_SECRET="yER8UxvSY0klei4vveGAJltJk5uQDYIyYtnU6ctH6cM"

# API 키 암호화
ENCRYPTION_KEY="f_4ye2tp9hFz49YH04Dc7fCITNdChxH9_0Q25ry-Sfw="

# JWT 인증
SECRET_KEY="09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"

# 데이터베이스
DATABASE_URL="postgresql://user:password@localhost:5432/tradingbot"
```

**키 생성 방법:**
```bash
# WEBHOOK_SECRET 생성
python -c "import secrets; print(secrets.token_urlsafe(32))"

# ENCRYPTION_KEY 생성
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# SECRET_KEY 생성
openssl rand -hex 32
```

---

## 보안 시스템

### 🔐 API 키 암호화 시스템

**목적**: 사용자의 거래소 API 키를 안전하게 저장

**구현 방식**: AES-256 암호화 (Fernet)

#### 암호화 서비스
```python
# app/core/crypto.py

from app.core.crypto import crypto_service

# 암호화
encrypted = crypto_service.encrypt_api_credentials(
    api_key="user_api_key",
    api_secret="user_api_secret",
    passphrase="okx_passphrase"  # OKX만
)
# → {
#      "api_key": "암호화된_문자열",
#      "api_secret": "암호화된_문자열",
#      "passphrase": "암호화된_문자열"
#    }

# 복호화 (사용 시에만)
decrypted = crypto_service.decrypt_api_credentials(encrypted)
# → {
#      "api_key": "원본_api_key",
#      "api_secret": "원본_api_secret",
#      "passphrase": "원본_passphrase"
#    }
```

#### 보안 보장사항

✅ **평문 저장 절대 불가**
- API 키는 데이터베이스에 암호화된 상태로만 저장됨
- 복호화는 주문 실행 시에만 메모리에서 일시적으로 수행

✅ **사용자별 완전 격리**
- 각 사용자는 본인의 API 키만 조회 가능
- JWT/NextAuth 토큰 검증 필수

✅ **암호화 키 보안**
- ENCRYPTION_KEY는 환경변수로 관리
- 키 분실 시 기존 데이터 복구 불가 (백업 필수)
- 프로덕션 환경에서는 AWS Secrets Manager 권장

### 🛡️ 사용자 인증 시스템

#### 지원 인증 방식
```python
# app/core/auth.py

# 1. JWT 토큰 인증
GET /api/v1/accounts-secure/list
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# 2. NextAuth 세션 토큰 인증
Authorization: Bearer <session_token>
```

#### 인증 미들웨어 사용법
```python
from app.core.auth import get_current_user
from fastapi import Depends

@router.get("/protected-endpoint")
async def protected_route(
    current_user: User = Depends(get_current_user)
):
    # current_user는 인증된 User 객체
    # 인증 실패 시 자동으로 401 에러 반환
    return {"user_id": current_user.id}
```

---

## 데이터베이스 구조

### ERD (Entity Relationship Diagram)

```
User (사용자)
├─ id (PK)
├─ email (unique)
├─ name
├─ password (hashed)
└─ created_at

   ┃ 1:N
   ┗━━━━━━━━━━━━━━━━━━━━┓

ApiKey (거래소 API 키)
├─ id (PK)
├─ user_id (FK → User.id)
├─ exchange (binance, okx)
├─ api_key (encrypted)
├─ api_secret (encrypted)
├─ passphrase (encrypted, OKX only)
├─ testnet (boolean)
├─ is_active (boolean)
└─ created_at

Session (NextAuth 세션)
├─ id (PK)
├─ user_id (FK → User.id)
├─ session_token (unique)
└─ expires
```

### 주요 모델

#### User 모델
```python
# app/models/user.py

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    name = Column(String)
    password = Column(String)  # bcrypt hashed

    # Gamification
    total_xp = Column(Integer, default=0)
    level = Column(Integer, default=1)
    total_trades = Column(Integer, default=0)

    # Relationships
    api_keys = relationship("ApiKey", back_populates="user")
    sessions = relationship("Session", back_populates="user")
```

#### ApiKey 모델
```python
# app/models/api_key.py

class ApiKey(Base):
    __tablename__ = "api_keys"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"))
    exchange = Column(String)  # "binance" or "okx"
    api_key = Column(String)  # AES-256 encrypted
    api_secret = Column(String)  # AES-256 encrypted
    passphrase = Column(String, nullable=True)  # OKX only
    testnet = Column(Boolean, default=True)
    is_active = Column(Boolean, default=True)

    user = relationship("User", back_populates="api_keys")
```

### 마이그레이션 관리

#### Alembic 사용법
```bash
# 새 마이그레이션 생성
alembic revision --autogenerate -m "설명"

# 마이그레이션 적용
alembic upgrade head

# 롤백
alembic downgrade -1

# 현재 버전 확인
alembic current
```

---

## API 엔드포인트 가이드

### 🔓 Public API (인증 불필요)

#### Webhook 수신
```http
POST /api/v1/webhook/tradingview
Content-Type: application/json

{
  "account_id": "user_abc_key_xyz",  # DB의 ApiKey.id
  "exchange": "binance",
  "action": "long",
  "symbol": "BTCUSDT",
  "leverage": 10,
  "secret": "webhook_secret_key"
}

Response 200 OK:
{
  "success": true,
  "message": "LONG order executed on binance",
  "order_details": {
    "exchange": "binance",
    "action": "long",
    "symbol": "BTCUSDT",
    "results": {
      "entry": {...},
      "leverage": {...}
    }
  }
}
```

### 🔐 Protected API (인증 필수)

#### 1. API 키 등록
```http
POST /api/v1/accounts-secure/register
Authorization: Bearer <user_token>
Content-Type: application/json

{
  "exchange": "binance",
  "api_key": "user_binance_api_key",
  "api_secret": "user_binance_secret",
  "testnet": true
}

Response 200 OK:
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "exchange": "binance",
  "testnet": true,
  "is_active": true,
  "created_at": "2025-01-01T00:00:00"
}
```

#### 2. 등록된 API 키 목록 조회
```http
GET /api/v1/accounts-secure/list
Authorization: Bearer <user_token>

Response 200 OK:
{
  "accounts": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "exchange": "binance",
      "testnet": true,
      "is_active": true,
      "created_at": "2025-01-01T00:00:00"
    }
  ],
  "total": 1
}
```

#### 3. API 키 삭제
```http
DELETE /api/v1/accounts-secure/{account_id}
Authorization: Bearer <user_token>

Response 200 OK:
{
  "success": true,
  "message": "Account deleted successfully"
}
```

#### 4. API 키 활성화/비활성화
```http
POST /api/v1/accounts-secure/{account_id}/toggle
Authorization: Bearer <user_token>

Response 200 OK:
{
  "success": true,
  "account_id": "550e8400-e29b-41d4-a716-446655440000",
  "is_active": false
}
```

---

## 프론트엔드 통합 가이드

### React/Next.js 예시 코드

#### 1. API 키 등록 컴포넌트
```typescript
// components/ApiKeyRegistration.tsx

import { useSession } from 'next-auth/react';
import { useState } from 'react';

export function ApiKeyRegistration() {
  const { data: session } = useSession();
  const [formData, setFormData] = useState({
    exchange: 'binance',
    apiKey: '',
    apiSecret: '',
    passphrase: '', // OKX only
    testnet: true
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    const response = await fetch('http://localhost:8001/api/v1/accounts-secure/register', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${session?.accessToken}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        exchange: formData.exchange,
        api_key: formData.apiKey,
        api_secret: formData.apiSecret,
        passphrase: formData.exchange === 'okx' ? formData.passphrase : undefined,
        testnet: formData.testnet
      })
    });

    if (response.ok) {
      const data = await response.json();
      alert(`API 키가 안전하게 등록되었습니다! ID: ${data.id}`);
    } else {
      const error = await response.json();
      alert(`등록 실패: ${error.detail}`);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <select value={formData.exchange} onChange={(e) => setFormData({...formData, exchange: e.target.value})}>
        <option value="binance">Binance</option>
        <option value="okx">OKX</option>
      </select>

      <input
        type="text"
        placeholder="API Key"
        value={formData.apiKey}
        onChange={(e) => setFormData({...formData, apiKey: e.target.value})}
        required
      />

      <input
        type="password"
        placeholder="API Secret"
        value={formData.apiSecret}
        onChange={(e) => setFormData({...formData, apiSecret: e.target.value})}
        required
      />

      {formData.exchange === 'okx' && (
        <input
          type="password"
          placeholder="Passphrase (OKX only)"
          value={formData.passphrase}
          onChange={(e) => setFormData({...formData, passphrase: e.target.value})}
          required
        />
      )}

      <label>
        <input
          type="checkbox"
          checked={formData.testnet}
          onChange={(e) => setFormData({...formData, testnet: e.target.checked})}
        />
        테스트넷 사용 (권장)
      </label>

      <button type="submit">API 키 등록</button>
    </form>
  );
}
```

#### 2. 등록된 API 키 목록
```typescript
// components/ApiKeyList.tsx

import { useSession } from 'next-auth/react';
import { useEffect, useState } from 'react';

interface ApiKey {
  id: string;
  exchange: string;
  testnet: boolean;
  is_active: boolean;
  created_at: string;
}

export function ApiKeyList() {
  const { data: session } = useSession();
  const [apiKeys, setApiKeys] = useState<ApiKey[]>([]);

  useEffect(() => {
    fetchApiKeys();
  }, [session]);

  const fetchApiKeys = async () => {
    if (!session) return;

    const response = await fetch('http://localhost:8001/api/v1/accounts-secure/list', {
      headers: {
        'Authorization': `Bearer ${session.accessToken}`
      }
    });

    const data = await response.json();
    setApiKeys(data.accounts);
  };

  const handleDelete = async (id: string) => {
    if (!confirm('정말 삭제하시겠습니까?')) return;

    await fetch(`http://localhost:8001/api/v1/accounts-secure/${id}`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${session?.accessToken}`
      }
    });

    fetchApiKeys(); // 목록 새로고침
  };

  const handleToggle = async (id: string) => {
    await fetch(`http://localhost:8001/api/v1/accounts-secure/${id}/toggle`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${session?.accessToken}`
      }
    });

    fetchApiKeys();
  };

  return (
    <div>
      <h2>등록된 API 키</h2>
      {apiKeys.map((key) => (
        <div key={key.id}>
          <span>{key.exchange} ({key.testnet ? 'Testnet' : 'Mainnet'})</span>
          <span>{key.is_active ? '활성' : '비활성'}</span>
          <button onClick={() => handleToggle(key.id)}>토글</button>
          <button onClick={() => handleDelete(key.id)}>삭제</button>
        </div>
      ))}
    </div>
  );
}
```

---

## 배포 및 운영

### 프로덕션 환경 설정

#### 1. 환경변수 보안
```bash
# .env.production
DEBUG=False
WEBHOOK_SECRET="production_webhook_secret_here"
ENCRYPTION_KEY="production_encryption_key_here"
DATABASE_URL="postgresql://user:password@production-db:5432/tradingbot"

# AWS Secrets Manager 사용 (권장)
AWS_SECRET_NAME="tradingbot/production"
AWS_REGION="us-east-1"
```

#### 2. HTTPS 필수
```nginx
# nginx.conf
server {
    listen 443 ssl;
    server_name your-domain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location /api/ {
        proxy_pass http://localhost:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

#### 3. 데이터베이스 백업
```bash
# 자동 백업 스크립트
#!/bin/bash
# backup.sh

DATE=$(date +%Y%m%d_%H%M%S)
pg_dump -h localhost -U tradingbot tradingbot > /backups/tradingbot_$DATE.sql

# 7일 이상 된 백업 삭제
find /backups -name "tradingbot_*.sql" -mtime +7 -delete
```

#### 4. 모니터링
```python
# app/core/monitoring.py

import logging
from prometheus_client import Counter, Histogram

# 메트릭 정의
webhook_requests = Counter('webhook_requests_total', 'Total webhook requests')
order_execution_time = Histogram('order_execution_seconds', 'Order execution time')

# 사용 예시
@webhook_requests.count_exceptions()
async def execute_order():
    with order_execution_time.time():
        # 주문 실행 로직
        pass
```

### 보안 체크리스트

프로덕션 배포 전 필수 확인사항:

- [ ] **HTTPS 적용** (Let's Encrypt 권장)
- [ ] **환경변수 보안** (AWS Secrets Manager)
- [ ] **데이터베이스 백업** (일일 자동 백업)
- [ ] **API 키 암호화 검증** (ENCRYPTION_KEY 백업)
- [ ] **로그 모니터링** (CloudWatch, Sentry)
- [ ] **Rate Limiting** (DDoS 방어)
- [ ] **IP Whitelist** (거래소 API 키)
- [ ] **테스트넷 검증** (최소 1주일)

---

## 문제 해결 가이드

### 자주 발생하는 이슈

#### 1. "Invalid webhook secret" 에러
```
원인: WEBHOOK_SECRET 불일치
해결: .env 파일과 TradingView 알림 메시지의 secret 값 확인
```

#### 2. "User not found" 에러
```
원인: JWT 토큰 또는 세션 토큰 만료
해결: 프론트엔드에서 토큰 갱신 또는 재로그인
```

#### 3. "Decryption failed" 에러
```
원인: ENCRYPTION_KEY 변경됨
해결: 기존 ENCRYPTION_KEY 복구 (백업 필수)
주의: ENCRYPTION_KEY 분실 시 기존 API 키 복구 불가능
```

#### 4. "Insufficient balance" 에러
```
원인: 거래소 계정 잔액 부족
해결: 거래소 계정에 USDT 입금
```

---

## 개발자 참고사항

### 코드 컨벤션

**Python (Backend):**
- PEP 8 준수
- Type hints 사용
- Docstring 필수 (Google style)

**TypeScript (Frontend):**
- ESLint + Prettier
- Strict mode 활성화

### Git Workflow

```bash
# Feature 브랜치 생성
git checkout -b feature/webhook-system

# 커밋
git commit -m "feat: Add TradingView webhook support"

# PR 생성 후 리뷰
# main 브랜치로 머지
```

### 테스트 가이드

```python
# tests/test_crypto.py

from app.core.crypto import crypto_service

def test_encryption_decryption():
    original = "test_api_key"
    encrypted = crypto_service.encrypt(original)
    decrypted = crypto_service.decrypt(encrypted)

    assert decrypted == original
    assert encrypted != original
```

---

## 추가 자료

- **TradingView Webhook 가이드**: `TRADINGVIEW_WEBHOOK_GUIDE.md`
- **API 문서**: http://localhost:8001/docs (FastAPI Swagger)
- **데이터베이스 스키마**: `alembic/versions/`

**작성자**: Claude AI Assistant
**프로젝트**: TradingBot AI
**라이선스**: MIT
