# 빠른 시작 가이드

5분 안에 TradingBot AI를 시작하는 방법을 알아보세요.

## 📋 준비물

- [ ] Binance 또는 OKX 계정
- [ ] TradingView 계정 (무료 가능)
- [ ] 이메일 주소

## 🚀 5단계 시작하기

### 1단계: 회원가입 (1분)

웹사이트 접속: `https://trendy.storydot.kr/trading`

```
1. 상단 "Sign Up" 클릭
2. 이메일, 비밀번호 입력
3. 이메일 인증 완료
4. 로그인
```

### 2단계: API 키 등록 (2분)

**⚠️ 주의: 처음에는 반드시 Testnet 사용!**

#### Binance Testnet API 키 발급
1. [Binance Testnet](https://testnet.binancefuture.com) 접속
2. GitHub 계정으로 로그인
3. API Key 생성:
   - API Key 복사
   - Secret Key 복사
   - **출금 권한 비활성화**

#### 시스템에 등록
```
Dashboard → Settings → API Keys → Register New API Key

Exchange: Binance
API Key: (복사한 API Key)
API Secret: (복사한 Secret Key)  
Testnet: ✅ 체크
```

**등록 성공 시 API Key ID가 표시됩니다 → 복사해두세요!**

### 3단계: Trading Config 설정 (1분)

```
Settings → Trading Config → Create Configuration

API Key: (방금 등록한 API Key 선택)
Strategy: SuperTrend
Investment Type: percentage
Investment Value: 0.1 (= 잔액의 10%)
Leverage: 5 (5배 레버리지)
Stop Loss %: 3
Take Profit %: 5
```

**Save** 클릭

### 4단계: Webhook 생성 (30초)

```
Webhooks → Create Webhook

Name: BTCUSDT Auto Trade
Description: 비트코인 자동매매 테스트
```

**Create** 클릭 후:
- `webhook_url` 복사
- `secret_token` 복사 (매우 중요!)

### 5단계: TradingView 설정 (1분)

Pine Script 작성 및 알림 설정은 [TradingView 통합 가이드](../guides/tradingview-integration.md)를 참조하세요.

## ✅ 완료! 이제 자동매매가 실행됩니다

### 확인 방법

1. **Dashboard**: 실시간 포지션 확인
2. **Trades 페이지**: 거래 내역 확인
3. **Analytics**: 수익률 차트 확인

## ⚠️ 주의사항

### 절대 하지 말아야 할 것

1. ❌ 테스트 없이 실전 투입
2. ❌ 전 재산 투입
3. ❌ 높은 레버리지 (20배 이상)
4. ❌ 손절 없이 거래
5. ❌ API 키 공유/공개

### 반드시 해야 할 것

1. ✅ 테스트넷으로 충분히 연습
2. ✅ 손절/익절 설정
3. ✅ 소액으로 시작
4. ✅ 지속적인 모니터링
5. ✅ 2FA 활성화
