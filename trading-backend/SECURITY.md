# 🔐 보안 강화 가이드

## 개요

TradingBot AI 시스템의 보안 강화 사항 및 모범 사례를 문서화합니다.

---

## ✅ 구현된 보안 기능

### 1. **API 키 암호화 (AES-256)**

**구현 위치**: `app/core/crypto.py`

```python
from app.core.crypto import crypto_service

# API 키 암호화
encrypted = crypto_service.encrypt_api_credentials(
    api_key="your_api_key",
    api_secret="your_api_secret",
    passphrase="your_passphrase"  # OKX only
)

# API 키 복호화
decrypted = crypto_service.decrypt_api_credentials(encrypted)
```

**특징**:
- AES-256 대칭 암호화 (Fernet)
- ENCRYPTION_KEY는 환경변수로 관리
- 데이터베이스에는 암호화된 값만 저장
- 복호화는 주문 실행 시점에만 수행

---

### 2. **사용자 인증 시스템**

**구현 위치**: `app/core/auth.py`

```python
from app.core.auth import get_current_user

@router.post("/protected-endpoint")
async def protected_route(current_user: User = Depends(get_current_user)):
    # 인증된 사용자만 접근 가능
    pass
```

**지원 인증 방식**:
- **JWT 토큰**: 자체 발급 JWT 토큰
- **NextAuth 세션**: 프론트엔드 NextAuth 세션 토큰

**검증 순서**:
1. JWT 토큰 검증 시도
2. 실패 시 NextAuth 세션 토큰 검증
3. 모두 실패 시 401 Unauthorized

---

### 3. **Webhook 보안**

**구현 위치**: `app/api/v1/webhook.py`

#### 3.1 Secret 검증
```python
# TradingView에서 보낸 secret과 서버의 WEBHOOK_SECRET 비교
if not verify_webhook_secret(webhook.secret, settings.WEBHOOK_SECRET):
    raise HTTPException(status_code=401, detail="Invalid webhook secret")
```

#### 3.2 입력 검증 강화
```python
class TradingViewWebhook(BaseModel):
    # 길이 제한
    account_id: str = Field(..., min_length=1, max_length=100)
    exchange: str = Field(..., min_length=3, max_length=20)

    # 양수 검증
    price: Optional[float] = Field(None, gt=0)
    quantity: Optional[float] = Field(None, gt=0)

    # 레버리지 범위 검증
    leverage: Optional[int] = Field(None, ge=1, le=125)

    # Secret 길이 검증 (최소 32자)
    secret: str = Field(..., min_length=32, max_length=128)
```

#### 3.3 Replay Attack 방지
```python
# 타임스탬프 검증 (±5분 허용)
timestamp: Optional[int] = Field(None, description="요청 타임스탬프")

@validator('timestamp')
def validate_timestamp(cls, v):
    if v is None:
        return v

    current_time = datetime.utcnow().timestamp()
    time_diff = abs(current_time - v)

    if time_diff > 300:  # 5분 = 300초
        raise ValueError("Request timestamp too old")

    return v
```

#### 3.4 심볼 화이트리스트
```python
# USDT 페어만 허용
SYMBOL_PATTERN = re.compile(r'^[A-Z0-9]{3,12}USDT$')

@validator('symbol')
def validate_symbol(cls, v):
    symbol_upper = v.upper()
    if not SYMBOL_PATTERN.match(symbol_upper):
        raise ValueError("Invalid symbol format")
    return symbol_upper
```

---

### 4. **에러 핸들링**

**구현 위치**: `app/core/exceptions.py`

#### 4.1 커스텀 예외
```python
from app.core.exceptions import (
    AuthenticationError,
    AuthorizationError,
    ValidationError,
    ExchangeAPIError,
    OrderExecutionError,
    InsufficientBalanceError,
    RateLimitExceeded,
    EncryptionError
)

# 사용 예시
if not valid:
    raise ValidationError("Invalid input", field="account_id")
```

#### 4.2 보안 친화적 에러 응답
```python
# 프로덕션 환경에서는 상세 에러 정보 숨김
if settings.DEBUG:
    error_detail = str(exc)
else:
    error_detail = "Internal server error"  # 일반 메시지만 반환
```

---

### 5. **구조화된 로깅**

**구현 위치**: `app/core/logging_config.py`

#### 5.1 보안 이벤트 로깅
```python
from app.core.logging_config import log_security_event

# 보안 이벤트 기록
log_security_event(
    event_type="unauthorized_access_attempt",
    user_id=user_id,
    ip_address=request.client.host,
    details={"path": request.url.path}
)
```

#### 5.2 로그 파일 분리
```
logs/
├── app.log          # 일반 애플리케이션 로그
├── error.log        # 에러 로그
└── security.log     # 보안 이벤트 로그 (인증 실패, 의심스러운 요청 등)
```

#### 5.3 JSON 구조화 로그
```json
{
  "timestamp": "2025-01-18T00:00:00.000000",
  "level": "WARNING",
  "logger": "security",
  "message": "Security event: unauthorized_access_attempt",
  "user_id": "user123",
  "ip_address": "192.168.1.100",
  "event_type": "unauthorized_access_attempt"
}
```

---

### 6. **환경별 설정 분리**

**구현 위치**: `app/core/config.py`

#### 6.1 환경 파일
```
.env.development   # 개발 환경 (testnet, DEBUG=True)
.env.production    # 프로덕션 환경 (mainnet, DEBUG=False, 엄격한 보안)
```

#### 6.2 프로덕션 환경 검증
```python
def validate_production_settings(self):
    """프로덕션 환경 설정 검증"""
    errors = []

    if self.DEBUG:
        errors.append("DEBUG must be False in production")

    if "generate" in self.SECRET_KEY.lower():
        errors.append("SECRET_KEY must be secure in production")

    if not self.ENCRYPTION_KEY:
        errors.append("ENCRYPTION_KEY must be set in production")

    if errors:
        raise ValueError(f"Production configuration errors: {errors}")
```

#### 6.3 환경 전환
```bash
# 개발 환경
export ENVIRONMENT=development
python main.py

# 프로덕션 환경
export ENVIRONMENT=production
python main.py
```

---

## 🛡️ 보안 체크리스트

### 개발 환경 설정
- [ ] `.env.development` 파일 생성
- [ ] 테스트넷 API 키 사용 (`BINANCE_TESTNET=True`)
- [ ] 개발용 시크릿 키 생성
- [ ] `DEBUG=True` 설정

### 프로덕션 배포 전
- [ ] `.env.production` 파일 생성
- [ ] 프로덕션용 시크릿 키 생성 (절대 재사용 금지)
  ```bash
  # SECRET_KEY
  openssl rand -hex 32

  # WEBHOOK_SECRET
  python -c "import secrets; print(secrets.token_urlsafe(32))"

  # ENCRYPTION_KEY
  python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
  ```
- [ ] `DEBUG=False` 설정
- [ ] 강력한 데이터베이스 비밀번호 설정
- [ ] HTTPS 활성화 및 SSL 인증서 설정
- [ ] 거래소 API 키 권한 최소화 (출금 권한 제거)
- [ ] 거래소 API 키 IP 화이트리스트 설정
- [ ] 방화벽 규칙 설정
- [ ] 로그 모니터링 시스템 구축

### 운영 중 보안 관리
- [ ] 정기적인 보안 로그 검토 (`logs/security.log`)
- [ ] 비정상 접근 시도 모니터링
- [ ] API 키 정기 교체 (3-6개월마다)
- [ ] 데이터베이스 백업 및 암호화
- [ ] 시스템 패치 및 업데이트
- [ ] 침투 테스트 (Penetration Testing)

---

## 🚨 보안 사고 대응

### 1. API 키 유출 시
1. **즉시 조치**:
   - 거래소에서 API 키 삭제
   - 새 API 키 생성 및 교체
   - 데이터베이스에서 암호화된 키 업데이트

2. **영향 분석**:
   - `logs/security.log` 검토
   - 비정상 거래 내역 확인
   - 자금 이동 내역 확인

3. **재발 방지**:
   - IP 화이트리스트 활성화
   - API 키 권한 최소화
   - 모니터링 알림 설정

### 2. 무단 접근 시도
1. **즉시 조치**:
   - IP 차단 (방화벽 규칙 추가)
   - 보안 로그 분석

2. **검토**:
   - 접근 패턴 분석
   - 취약점 식별

3. **강화**:
   - Rate limiting 활성화
   - WAF (Web Application Firewall) 설정

### 3. 데이터베이스 침해 시
1. **즉시 조치**:
   - 서비스 중단
   - 데이터베이스 접근 차단

2. **복구**:
   - 백업에서 복원
   - 모든 사용자 비밀번호 초기화
   - 새 ENCRYPTION_KEY 생성

---

## 📋 보안 모범 사례

### 1. **최소 권한 원칙**
- API 키는 필요한 권한만 부여
- 거래소 API 키: "Enable Futures" 권한만 (출금 권한 제거)

### 2. **심층 방어**
- 다중 보안 계층 구현
- 암호화 + 인증 + 입력 검증 + 로깅

### 3. **보안 업데이트**
- 정기적인 의존성 패키지 업데이트
  ```bash
  pip list --outdated
  pip install --upgrade <package>
  ```

### 4. **민감 정보 분리**
- 환경변수로 관리 (`.env` 파일)
- 절대 버전 관리에 커밋하지 않음
- `.gitignore`에 `.env*` 추가

### 5. **감사 로그**
- 모든 중요 작업 로깅
- 로그 무결성 보장
- 정기적인 로그 검토

---

## 🔗 관련 문서

- [CLAUDE.md](CLAUDE.md) - 전체 시스템 아키텍처
- [TRADINGVIEW_WEBHOOK_GUIDE.md](TRADINGVIEW_WEBHOOK_GUIDE.md) - Webhook 설정 가이드
- [README.md](../README.md) - 프로젝트 개요

---

## 📞 보안 문제 보고

보안 취약점을 발견하신 경우:
1. **즉시 보고**: security@yourdomain.com (이메일 변경 필요)
2. **비공개 보고**: GitHub Security Advisory (비공개)
3. **보고 내용**:
   - 취약점 설명
   - 재현 방법
   - 영향 범위
   - 제안하는 해결책

**⚠️ 공개 이슈로 보안 문제를 보고하지 마세요!**

---

**마지막 업데이트**: 2025-01-18
**작성자**: TradingBot AI Development Team
