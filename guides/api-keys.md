# API 키 등록 가이드

거래소 API 키를 안전하게 등록하는 방법을 알아보세요.

## 🔑 API 키란?

**API 키**는 프로그램이 거래소 계정에 접근할 수 있게 하는 인증 정보입니다.

## 📋 준비사항

- [ ] Binance 또는 OKX 계정
- [ ] 이메일 인증 완료
- [ ] 2FA (2단계 인증) 활성화 권장

## ⚠️ 중요: Testnet부터 시작하세요!

### Testnet이란?

**Testnet**은 실제 돈을 사용하지 않는 테스트 환경입니다.

| 구분 | Mainnet | Testnet |
|------|---------|---------|
| 실제 돈 | ✅ 사용 | ❌ 가상 |
| 위험도 | 🔴 높음 | 🟢 없음 |
| 목적 | 실제 거래 | 연습/테스트 |

## 🚀 Binance Testnet API 키 발급

### 1단계: Testnet 접속

[Binance Futures Testnet](https://testnet.binancefuture.com/) 접속

### 2단계: GitHub 로그인

```
1. GitHub 계정으로 로그인
2. Authorize 클릭
```

### 3단계: API Key 생성

```
1. 우측 상단 프로필 → API Keys
2. Create New Key
3. Label: TradingBot AI
4. API restrictions:
   ✅ Enable Reading
   ✅ Enable Futures
   ❌ Enable Withdrawals (출금 권한 비활성화)
```

### 4단계: API 키 복사

```
API Key: abcdefghijklmnopqrstuvwxyz1234567890
Secret Key: ABCDEFGHIJKLMNOPQRSTUVWXYZ0987654321

⚠️ Secret Key는 한 번만 표시됩니다!
⚠️ 안전한 곳에 저장하세요!
```

## 🔐 시스템에 등록

### 1단계: Settings 페이지 접속

```
Dashboard → 좌측 메뉴 → Settings
```

### 2단계: API Keys 섹션

```
API Keys → Register New API Key 클릭
```

### 3단계: 정보 입력

```
Exchange: Binance
API Key: (복사한 API Key)
API Secret: (복사한 Secret Key)
Testnet: ✅ 체크 (매우 중요!)
```

### 4단계: Register 클릭

등록 성공 시:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "exchange": "binance",
  "testnet": true,
  "is_active": true,
  "created_at": "2025-01-01T00:00:00"
}
```

**⭐ API Key ID를 복사하세요!** (Webhook 설정에 사용)

## 🌐 OKX Testnet API 키 발급

### 1단계: OKX Testnet 접속

[OKX Demo Trading](https://www.okx.com/demo-trading) 접속

### 2단계: 계정 생성

```
1. Sign Up
2. Email/Password 입력
3. 이메일 인증
```

### 3단계: API Key 생성

```
1. Profile → API Management
2. Create API Key
3. API Key Name: TradingBot AI
4. Passphrase: 강력한 비밀번호 설정 (기억하세요!)
5. IP Whitelist: (선택사항)
6. Permissions:
   ✅ Read
   ✅ Trade
   ❌ Withdraw
```

### 4단계: 3개 정보 복사

```
API Key: okx-api-key-here
Secret Key: okx-secret-key-here
Passphrase: your-passphrase-here

⚠️ 3개 모두 필요합니다!
```

### 5단계: 시스템에 등록

```
Exchange: OKX
API Key: (복사한 API Key)
API Secret: (복사한 Secret Key)
Passphrase: (설정한 Passphrase)
Testnet: ✅ 체크
```

## 🔒 보안 모범 사례

### 1. API 키 권한 최소화

```
✅ Enable Reading (읽기)
✅ Enable Trading (거래)
❌ Enable Withdrawals (출금) - 절대 활성화 금지!
```

### 2. IP Whitelist 설정 (권장)

```
AWS 서버 IP: 13.239.192.158
또는
본인 고정 IP 주소
```

### 3. 주기적인 키 갱신

```
권장: 3개월마다 새 API 키 생성
1. 새 API 키 발급
2. 시스템에 등록
3. 테스트 후 기존 키 삭제
```

### 4. API 키 노출 주의

```
❌ GitHub 코드에 포함
❌ 스크린샷 공유
❌ 공개 포럼에 질문 시 노출
✅ 환경 변수로 관리
✅ .env 파일 (gitignore 추가)
```

## 🔐 암호화 시스템

### AES-256 암호화

TradingBot AI는 모든 API 키를 **AES-256**으로 암호화하여 저장합니다:

```
입력: API Key (평문)
    ↓
AES-256 암호화
    ↓
저장: 암호화된 문자열
    ↓
사용 시에만 복호화 (메모리)
    ↓
사용 후 즉시 삭제
```

### 데이터베이스 구조

```sql
CREATE TABLE api_keys (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL,
    exchange VARCHAR NOT NULL,
    api_key TEXT NOT NULL,       -- AES-256 암호화
    api_secret TEXT NOT NULL,    -- AES-256 암호화
    passphrase TEXT,             -- AES-256 암호화 (OKX)
    testnet BOOLEAN DEFAULT true,
    is_active BOOLEAN DEFAULT true
);
```

**평문 저장 절대 금지!**

## 🧪 API 키 테스트

### 연결 확인

```
Settings → API Keys → 등록된 키 옆 Test Connection

성공:
✅ Connection successful
✅ Balance: 10,000 USDT

실패:
❌ Invalid API Key
❌ IP not whitelisted
❌ Insufficient permissions
```

### 잔액 확인

```
Dashboard → 상단에 표시
Testnet: 10,000 USDT (기본 지급)
```

## 📊 여러 API 키 관리

### 다중 계정 지원

```
1. Binance Testnet
2. Binance Mainnet  
3. OKX Testnet
4. OKX Mainnet

⚠️ 각각 별도 Trading Config 필요
```

### 활성화/비활성화

```
Settings → API Keys → Toggle Active

is_active = false로 설정 시:
- 새로운 주문 차단
- 기존 포지션은 유지
- 언제든지 재활성화 가능
```

## ⚠️ 자주 발생하는 문제

### "Invalid API Key" 에러

**원인**:
- API Key/Secret 복사 시 공백 포함
- 잘못된 키 입력

**해결**:
1. API Key 재생성
2. 복사 시 앞뒤 공백 제거
3. 다시 등록

### "IP not whitelisted" 에러

**원인**:
- 거래소에서 IP Whitelist 설정됨

**해결**:
1. 거래소 API 설정에서 IP 추가
2. 또는 Whitelist 비활성화

### "Insufficient permissions" 에러

**원인**:
- API 키에 Trading 권한 없음

**해결**:
1. 거래소 API 설정 확인
2. Enable Trading 체크
3. 새 키 발급 후 재등록

## 📚 다음 단계

- [Trading Config 설정](trading-config.md)
- [Webhook 설정](webhook-setup.md)
- [보안 모범 사례](../security/best-practices.md)
