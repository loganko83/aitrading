# TradingBot AI 사용자 가이드

**AI 기반 암호화폐 자동매매 시스템**

TradingBot AI는 TradingView 알림과 연동하여 Binance 및 OKX 거래소에서 자동으로 거래를 실행하는 시스템입니다.

## 🚀 주요 기능

### 📊 6가지 AI 트레이딩 전략
- **SuperTrend**: 추세 추종 전략
- **RSI + EMA**: 과매수/과매도 + 이동평균 조합
- **MACD + Stochastic**: 모멘텀 + 스토캐스틱 조합
- **Ichimoku Cloud**: 일목균형표 기반 전략
- **Bollinger Bands + RSI**: 볼린저 밴드 + RSI 조합
- **EMA Crossover**: 이동평균선 교차 전략

### 🔐 보안 시스템
- **AES-256 암호화**: 거래소 API 키 안전하게 저장
- **JWT 인증**: 사용자별 격리된 환경
- **HMAC-SHA256**: Webhook 서명 검증
- **NextAuth**: 2FA 지원 (TOTP)

### 🎯 TradingView 통합
- **Pine Script 자동 생성**: 전략을 Pine Script로 변환
- **Webhook 자동 주문**: TradingView 알림 → 실제 거래
- **실시간 시그널**: 지연 없이 주문 전송

### 🌐 다중 거래소 지원
- **Binance Futures**: 레버리지 최대 125배
- **OKX Futures**: Swap 계약 지원
- **테스트넷 지원**: 실제 돈 사용 전 연습

### 📈 백테스팅 엔진
- 과거 데이터 기반 성과 분석
- 승률, 손익, MDD 계산
- 파라미터 최적화

## 📖 가이드 구조

### 시작하기
- [빠른 시작 가이드](getting-started/quick-start.md)
- [설치 및 설정](getting-started/installation.md)
- [첫 거래 실행](getting-started/first-trade.md)

### 사용 가이드
- [API 키 등록](guides/api-keys.md)
- [Trading Config 설정](guides/trading-config.md)
- [Webhook 설정](guides/webhook-setup.md)
- [TradingView 통합](guides/tradingview-integration.md)
- [전략 선택 가이드](guides/strategy-selection.md)

### 전략 상세
- [전략 개요](strategies/overview.md)
- [SuperTrend 전략](strategies/supertrend.md)
- [RSI + EMA 전략](strategies/rsi-ema.md)
- [MACD + Stochastic 전략](strategies/macd-stochastic.md)
- [Ichimoku Cloud 전략](strategies/ichimoku.md)
- [Bollinger Bands + RSI 전략](strategies/bollinger-rsi.md)
- [EMA Crossover 전략](strategies/ema-crossover.md)

### 보안
- [암호화 시스템](security/encryption.md)
- [보안 모범 사례](security/best-practices.md)
- [2단계 인증 (2FA)](security/two-factor-auth.md)

### 문제 해결
- [자주 묻는 질문 (FAQ)](troubleshooting/faq.md)
- [일반적인 문제](troubleshooting/common-issues.md)
- [에러 코드 참조](troubleshooting/error-codes.md)

### API 참조
- [인증](api-reference/authentication.md)
- [엔드포인트](api-reference/endpoints.md)
- [Webhook API](api-reference/webhook-api.md)

## ⚠️ 중요 안전 수칙

### 1. 테스트넷으로 시작하세요
```
⛔ 처음부터 실제 거래소 사용 금지
✅ 반드시 Testnet으로 연습 (최소 1주일)
✅ 전략 검증 후 실전 투입
```

### 2. 소액으로 시작하세요
```
⛔ 전 재산을 투입하지 마세요
✅ 잃어도 괜찮은 금액만 사용
✅ 레버리지는 낮게 시작 (5배 이하 권장)
```

### 3. API 키를 안전하게 관리하세요
```
⛔ GitHub, 포럼에 API 키 공개 금지
⛔ 스크린샷 공유 시 API 키 노출 주의
✅ IP Whitelist 설정 (거래소 설정)
✅ 출금 권한은 비활성화
```

### 4. 손절/익절을 반드시 설정하세요
```
⛔ 손절 없이 거래 금지
✅ Stop Loss: 2-3% 권장
✅ Take Profit: 5-10% 권장
✅ 레버리지가 높을수록 손절폭 좁게
```

## 📊 권장 설정

### 초보자
```yaml
투자 금액: 100-500 USDT (테스트넷)
레버리지: 3-5배
손절: 3%
익절: 5%
전략: SuperTrend (가장 단순)
```

### 중급자
```yaml
투자 금액: 500-2000 USDT
레버리지: 5-10배
손절: 2%
익절: 7%
전략: RSI + EMA 또는 MACD + Stochastic
```

### 고급자
```yaml
투자 금액: 2000+ USDT
레버리지: 10-20배
손절: 1-2%
익절: 10-15%
전략: Ichimoku 또는 커스텀 조합
```

## 🎓 학습 로드맵

### 1주차: 기본 이해
- [ ] 시스템 설치 및 회원가입
- [ ] API 키 등록 (테스트넷)
- [ ] Trading Config 설정
- [ ] 첫 Webhook 생성

### 2주차: TradingView 연동
- [ ] Pine Script 기본 학습
- [ ] SuperTrend 전략 적용
- [ ] 알림 설정 및 테스트
- [ ] 백테스팅으로 검증

### 3주차: 전략 최적화
- [ ] 다양한 전략 테스트
- [ ] 파라미터 조정
- [ ] 승률 및 손익 분석
- [ ] 최적 설정 발견

### 4주차: 실전 투입
- [ ] 테스트넷 성과 검토
- [ ] 실제 거래소 API 키 등록
- [ ] 소액으로 실전 시작
- [ ] 지속적인 모니터링

## 📞 지원

- **GitHub Issues**: [문제 신고](https://github.com/your-repo/issues)
- **Discord**: [커뮤니티 참여](#)
- **이메일**: support@tradingbot.ai

## 📄 라이선스

MIT License - 자유롭게 사용 및 수정 가능

---

**면책 조항**: 암호화폐 거래는 높은 위험을 수반합니다. 이 시스템을 사용하여 발생하는 모든 손실에 대해 개발자는 책임지지 않습니다. 투자 결정은 본인의 책임 하에 이루어져야 합니다.
