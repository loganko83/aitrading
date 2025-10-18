# 🏗️ TradingBot AI - 완전 자동매매 시스템 아키텍처

**버전**: v2.0.0
**최종 업데이트**: 2025-01-18
**상태**: 설계 완료, 구현 진행 중

---

## 📋 목차

1. [시스템 개요](#시스템-개요)
2. [전체 플로우](#전체-플로우)
3. [기술 스택](#기술-스택)
4. [아키텍처 다이어그램](#아키텍처-다이어그램)
5. [백엔드 아키텍처](#백엔드-아키텍처)
6. [프론트엔드 아키텍처](#프론트엔드-아키텍처)
7. [보안 아키텍처](#보안-아키텍처)
8. [데이터베이스 설계](#데이터베이스-설계)
9. [API 설계](#api-설계)
10. [배포 전략](#배포-전략)

---

## 시스템 개요

### 핵심 목표
**사용자가 클릭 몇 번으로 완전 자동매매 시스템을 구축할 수 있는 플랫폼**

### 주요 특징
- ✅ **사용자 친화적 UI/UX**: 비개발자도 5분 내 설정 완료
- ✅ **완전 자동화**: AI 지표 설계 → TradingView 연동 → 자동 주문 → 수익률 알림
- ✅ **보안 최우선**: AES-256 암호화, 2FA, Rate Limiting, IP 화이트리스트
- ✅ **실시간 모니터링**: WebSocket 기반 실시간 포지션/수익률 추적
- ✅ **리스크 관리**: 포지션 사이징, 손절/익절 자동화, 레버리지 제어

### 대상 사용자
- 암호화폐 자동매매를 시작하려는 초보자
- 수동 매매에서 자동화로 전환하려는 중급자
- 여러 전략을 동시에 운영하려는 고급 트레이더

---

## 전체 플로우

### 1️⃣ 사용자 온보딩 플로우
```
회원가입 (이메일 인증)
    ↓
2FA 설정 (Google Authenticator)
    ↓
거래소 API 키 등록 (Binance/OKX)
    ↓
텔레그램 봇 연동 (BotFather 토큰)
    ↓
전략 선택 또는 커스텀 설정
    ↓
백테스팅 (선택사항)
    ↓
실전 트레이딩 시작
```

### 2️⃣ 자동매매 실행 플로우
```
AI 지표 설계
  ├─ 최신 트렌드 분석 (GPT-4 + Claude)
  ├─ 차트 패턴 분석 (기술적 분석)
  ├─ 거래량 분석 (Volume Profile)
  └─ 프랙탈 현상 분석 (Fractal Geometry)
    ↓
TradingView Pine Script 인디케이터 설정
  ├─ 자동 생성된 Pine Script
  ├─ Webhook 알림 설정
  └─ 사용자 맞춤 파라미터 적용
    ↓
백엔드 Webhook 수신
  ├─ HMAC 서명 검증
  ├─ Replay Attack 방지
  └─ 주문 준비 (리스크 체크)
    ↓
Binance/OKX API 주문 실행
  ├─ 포지션 사이징 (계좌의 X%)
  ├─ 레버리지 설정 (사용자 지정)
  ├─ 손절/익절 주문 자동 설정
  └─ 주문 체결 확인
    ↓
텔레그램 주문 현황 알림
  ├─ 진입가, 수량, 레버리지
  ├─ 손절가, 익절가
  └─ 예상 손익
    ↓
AI 지속 분석
  ├─ 시장 상황 모니터링
  ├─ 포지션 리스크 평가
  └─ 조기 청산 권장 여부
    ↓
주요 수익률 텔레그램 알림
  ├─ 1% 이상 변동 시 실시간 알림
  ├─ 일일 수익률 리포트
  └─ 주간/월간 성과 요약
```

### 3️⃣ 사용자 프로세스 업데이트 플로우
```
사용자 로그인
    ↓
설정 페이지 접근
    ↓
① Binance/OKX API 설정
  ├─ API Key/Secret 입력
  ├─ 자동 암호화 (AES-256)
  ├─ 연결 테스트
  └─ IP 화이트리스트 확인
    ↓
② 텔레그램 봇 설정
  ├─ BotFather에서 토큰 발급
  ├─ 토큰 입력
  ├─ Chat ID 자동 확인
  └─ 테스트 알림 발송
    ↓
③ TradingView 인디케이터 설정
  ├─ 인디케이터 검색 (5개 템플릿 + 커스텀)
  ├─ 파라미터 조정 (EMA 기간, RSI 임계값 등)
  ├─ Webhook URL 자동 생성
  └─ Pine Script 복사 → TradingView 적용
    ↓
④ 본인만의 전략 설정
  ├─ 투입금: 전체 담보금(Deposit)의 몇 %
  ├─ 롱 진입 시 익절 목표: +X% (예: +5%)
  ├─ 롱 진입 시 손절 목표: -X% (예: -2%)
  ├─ 숏 진입 시 익절 목표: -X% (예: -5%)
  ├─ 숏 진입 시 손절 목표: +X% (예: +2%)
  └─ 선물 레버리지 배수: 1x ~ 125x
    ↓
⑤ 백테스팅 (선택사항)
  ├─ 과거 6개월 데이터로 시뮬레이션
  ├─ 예상 수익률, 최대 손실률 계산
  └─ 리스크/보상 비율 확인
    ↓
⑥ 실전 트레이딩 시작
  └─ 실시간 대시보드에서 모니터링
```

---

## 기술 스택

### Frontend (사용자 친화적 UI)
```yaml
Framework: Next.js 14 (App Router)
Language: TypeScript
Styling:
  - Tailwind CSS (유틸리티 기반 스타일링)
  - shadcn/ui (고품질 컴포넌트)
  - Framer Motion (애니메이션)
State Management:
  - Zustand (경량 상태 관리)
  - React Query (서버 상태 관리)
Real-time:
  - Socket.IO Client (실시간 포지션 업데이트)
Charts:
  - Recharts (수익률 차트)
  - TradingView Lightweight Charts (가격 차트)
Authentication:
  - NextAuth.js (세션 관리)
  - JWT (토큰 인증)
Form Validation:
  - React Hook Form + Zod
UI/UX:
  - 반응형 디자인 (모바일 우선)
  - 다크 모드 기본 제공
  - 접근성 준수 (WCAG 2.1 AA)
```

### Backend (안정적이고 보안 강화된 서버)
```yaml
Framework: FastAPI (Python 3.10+)
Language: Python (타입 힌트 필수)
Database:
  - PostgreSQL 15 (메인 데이터베이스)
  - Redis 7 (세션 캐시, Rate Limiting)
ORM: SQLAlchemy 2.0 (비동기 지원)
Authentication:
  - JWT (Access Token + Refresh Token)
  - bcrypt (비밀번호 해싱)
  - pyotp (2FA TOTP)
Security:
  - cryptography (AES-256 API 키 암호화)
  - slowapi (Rate Limiting)
  - python-jose (JWT 서명 검증)
Real-time:
  - Socket.IO (양방향 통신)
  - WebSocket (실시간 가격 피드)
AI/ML:
  - OpenAI API (GPT-4 분석)
  - Anthropic API (Claude 분석)
  - NumPy/Pandas (데이터 분석)
  - TA-Lib (기술적 지표)
Background Jobs:
  - Celery (비동기 작업 큐)
  - Redis (Celery 브로커)
Testing:
  - pytest (단위 테스트)
  - pytest-asyncio (비동기 테스트)
Monitoring:
  - Sentry (에러 추적)
  - Prometheus (메트릭 수집)
```

### DevOps & Infrastructure
```yaml
Containerization: Docker + Docker Compose
Reverse Proxy: Nginx
SSL/TLS: Let's Encrypt (자동 갱신)
CI/CD: GitHub Actions
Monitoring:
  - Grafana (시각화)
  - Prometheus (메트릭)
  - Loki (로그 수집)
Backup:
  - PostgreSQL 자동 백업 (일일)
  - S3 호환 스토리지
Environment: .env 파일로 환경 분리
```

---

## 아키텍처 다이어그램

### High-Level Architecture
```
┌─────────────────────────────────────────────────────────────┐
│                         사용자 (Browser)                      │
└─────────────────────┬───────────────────────────────────────┘
                      │ HTTPS
                      ↓
┌─────────────────────────────────────────────────────────────┐
│                    Nginx (Reverse Proxy)                     │
│                    - SSL Termination                         │
│                    - Rate Limiting                           │
│                    - Load Balancing                          │
└─────────────────────┬───────────────────────────────────────┘
                      │
        ┌─────────────┴─────────────┐
        ↓                           ↓
┌───────────────────┐      ┌────────────────────┐
│  Next.js Frontend │      │  FastAPI Backend   │
│  (Port 3000)      │←────→│  (Port 8001)       │
│                   │ API  │                    │
│  - 대시보드        │      │  - REST API        │
│  - 설정 페이지     │      │  - WebSocket       │
│  - 차트 시각화     │      │  - Webhook 수신    │
└───────────────────┘      └─────────┬──────────┘
                                     │
                    ┌────────────────┼────────────────┐
                    ↓                ↓                ↓
          ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
          │ PostgreSQL  │  │   Redis     │  │   Celery    │
          │ (메인 DB)   │  │  (캐시)     │  │ (백그라운드) │
          └─────────────┘  └─────────────┘  └─────────────┘
                                     │
                    ┌────────────────┼────────────────┐
                    ↓                ↓                ↓
          ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
          │  Binance    │  │    OKX      │  │  Telegram   │
          │   API       │  │    API      │  │  Bot API    │
          └─────────────┘  └─────────────┘  └─────────────┘
                                     │
                                     ↓
                          ┌─────────────────┐
                          │  TradingView    │
                          │   (Webhook)     │
                          └─────────────────┘
```

### Data Flow Architecture
```
[TradingView Pine Script]
        ↓ Webhook Alert
[FastAPI Webhook Endpoint]
        ↓ Validate HMAC
[Order Executor Service]
        ↓ Risk Check
[Binance/OKX API]
        ↓ Order Filled
[Telegram Service]
        ↓ Notification
[User Mobile Device]
        ↓ View Dashboard
[Next.js Frontend]
        ↓ WebSocket
[Real-time Position Updates]
```

---

## 백엔드 아키텍처

### 디렉토리 구조
```
trading-backend/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── auth.py               # 인증 (회원가입, 로그인, 2FA)
│   │       ├── users.py              # 사용자 관리
│   │       ├── accounts.py           # 거래소 API 키 관리
│   │       ├── strategies.py         # 전략 설정 (익절/손절/레버리지)
│   │       ├── trading.py            # 주문 실행
│   │       ├── webhook.py            # TradingView Webhook
│   │       ├── telegram.py           # 텔레그램 알림
│   │       ├── pine_script.py        # Pine Script AI
│   │       ├── backtest.py           # 백테스팅
│   │       ├── positions.py          # 포지션 관리 (NEW)
│   │       ├── performance.py        # 수익률 분석 (NEW)
│   │       └── websocket.py          # 실시간 데이터 (NEW)
│   ├── core/
│   │   ├── config.py                 # 환경 설정
│   │   ├── security.py               # 보안 (JWT, 암호화, 2FA)
│   │   ├── database.py               # 데이터베이스 연결
│   │   ├── exceptions.py             # 커스텀 예외
│   │   └── logging_config.py         # 로깅 설정
│   ├── models/
│   │   ├── user.py                   # User 모델 (NEW)
│   │   ├── api_key.py                # API 키 모델
│   │   ├── strategy.py               # 전략 모델 (확장)
│   │   ├── position.py               # 포지션 모델 (NEW)
│   │   ├── order.py                  # 주문 모델 (NEW)
│   │   └── performance.py            # 성과 모델 (NEW)
│   ├── services/
│   │   ├── auth_service.py           # 인증 서비스 (NEW)
│   │   ├── user_service.py           # 사용자 서비스 (NEW)
│   │   ├── order_executor.py         # 주문 실행 (확장)
│   │   ├── risk_manager.py           # 리스크 관리 (NEW)
│   │   ├── position_manager.py       # 포지션 관리 (NEW)
│   │   ├── telegram_service.py       # 텔레그램 알림
│   │   ├── pine_script_analyzer.py   # Pine Script 분석
│   │   ├── strategy_optimizer.py     # 전략 최적화
│   │   ├── ai_ensemble.py            # AI 앙상블 (확장)
│   │   └── market_analyzer.py        # 시장 분석 (NEW)
│   ├── utils/
│   │   ├── encryption.py             # AES-256 암호화
│   │   ├── validators.py             # 입력 검증 (NEW)
│   │   └── formatters.py             # 데이터 포맷팅 (NEW)
│   └── tasks/
│       ├── celery_app.py             # Celery 설정 (NEW)
│       ├── market_data.py            # 시장 데이터 수집 (NEW)
│       └── performance_calc.py       # 수익률 계산 (NEW)
├── alembic/                          # 데이터베이스 마이그레이션
├── tests/                            # 테스트 코드
├── main.py                           # FastAPI 애플리케이션
├── requirements.txt                  # Python 의존성
└── docker-compose.yml                # Docker 설정
```

### 핵심 서비스 설계

#### 1. AuthService (인증 서비스)
```python
class AuthService:
    """사용자 인증 및 권한 관리"""

    async def register_user(email, password) -> User:
        """회원가입 + 이메일 인증"""

    async def login(email, password) -> TokenPair:
        """로그인 (JWT 토큰 발급)"""

    async def verify_2fa(user_id, totp_code) -> bool:
        """2FA 검증 (Google Authenticator)"""

    async def refresh_token(refresh_token) -> AccessToken:
        """리프레시 토큰으로 액세스 토큰 갱신"""
```

#### 2. RiskManager (리스크 관리 서비스)
```python
class RiskManager:
    """포지션 사이징 및 리스크 제어"""

    async def calculate_position_size(account_id, strategy_config) -> float:
        """
        포지션 사이즈 계산
        - 전체 담보금의 X% 사용
        - 레버리지 고려
        - 최대 손실 한도 체크
        """

    async def set_stop_loss_take_profit(position, strategy_config) -> Order:
        """
        손절/익절 주문 자동 설정
        - 롱: 진입가 기준 +X% 익절, -X% 손절
        - 숏: 진입가 기준 -X% 익절, +X% 손절
        """

    async def check_risk_limits(user_id) -> RiskReport:
        """
        리스크 한도 체크
        - 일일 최대 손실률 초과 여부
        - 동시 포지션 개수 제한
        - 레버리지 제한
        """
```

#### 3. MarketAnalyzer (AI 시장 분석 서비스)
```python
class MarketAnalyzer:
    """AI 기반 시장 분석 (GPT-4 + Claude)"""

    async def analyze_chart_pattern(symbol, timeframe) -> ChartAnalysis:
        """
        차트 패턴 분석
        - 헤드앤숄더, 더블탑/바텀
        - 지지/저항선
        - 추세선
        """

    async def analyze_volume_profile(symbol) -> VolumeAnalysis:
        """
        거래량 프로파일 분석
        - POC (Point of Control)
        - Value Area
        - 거래량 급증 구간
        """

    async def analyze_fractal_geometry(symbol) -> FractalAnalysis:
        """
        프랙탈 현상 분석
        - 자기유사성 패턴
        - 프랙탈 차원 계산
        - 카오스 이론 적용
        """

    async def get_ai_recommendation(symbol) -> AIRecommendation:
        """
        AI 종합 추천
        - GPT-4 + Claude 듀얼 분석
        - 진입/청산 타이밍
        - 리스크 평가
        """
```

#### 4. PositionManager (포지션 관리 서비스)
```python
class PositionManager:
    """실시간 포지션 추적 및 관리"""

    async def get_active_positions(user_id) -> List[Position]:
        """활성 포지션 조회"""

    async def calculate_pnl(position) -> PnL:
        """
        실시간 손익 계산
        - 미실현 손익 (Unrealized PnL)
        - 실현 손익 (Realized PnL)
        - ROI, ROE 계산
        """

    async def monitor_positions(user_id) -> None:
        """
        포지션 모니터링 (백그라운드 작업)
        - 1% 이상 변동 시 텔레그램 알림
        - 손절/익절 도달 시 자동 청산
        - AI 조기 청산 권장
        """
```

---

## 프론트엔드 아키텍처

### 디렉토리 구조
```
trading-frontend/
├── app/
│   ├── (auth)/
│   │   ├── login/
│   │   │   └── page.tsx              # 로그인 페이지
│   │   ├── register/
│   │   │   └── page.tsx              # 회원가입 페이지
│   │   └── verify-2fa/
│   │       └── page.tsx              # 2FA 인증 페이지
│   ├── (dashboard)/
│   │   ├── layout.tsx                # 대시보드 레이아웃
│   │   ├── page.tsx                  # 메인 대시보드
│   │   ├── positions/
│   │   │   └── page.tsx              # 포지션 현황
│   │   ├── performance/
│   │   │   └── page.tsx              # 수익률 분석
│   │   └── history/
│   │       └── page.tsx              # 거래 내역
│   ├── (settings)/
│   │   ├── layout.tsx                # 설정 레이아웃
│   │   ├── exchanges/
│   │   │   └── page.tsx              # 거래소 API 설정
│   │   ├── telegram/
│   │   │   └── page.tsx              # 텔레그램 봇 설정
│   │   ├── indicators/
│   │   │   └── page.tsx              # TradingView 인디케이터 설정
│   │   └── strategy/
│   │       └── page.tsx              # 전략 설정 (익절/손절/레버리지)
│   └── api/
│       └── auth/
│           └── [...nextauth]/
│               └── route.ts          # NextAuth.js API 라우트
├── components/
│   ├── ui/                           # shadcn/ui 컴포넌트
│   ├── dashboard/
│   │   ├── PositionCard.tsx          # 포지션 카드
│   │   ├── PnLChart.tsx              # 손익 차트
│   │   └── RealTimePrice.tsx         # 실시간 가격
│   ├── settings/
│   │   ├── ExchangeAPIForm.tsx       # 거래소 API 입력 폼
│   │   ├── TelegramBotForm.tsx       # 텔레그램 봇 설정 폼
│   │   ├── IndicatorSelector.tsx     # 인디케이터 선택기
│   │   └── StrategyConfig.tsx        # 전략 설정 폼
│   └── layout/
│       ├── Sidebar.tsx               # 사이드바 네비게이션
│       └── Header.tsx                # 헤더
├── lib/
│   ├── api/
│   │   ├── client.ts                 # API 클라이언트
│   │   ├── auth.ts                   # 인증 API
│   │   ├── trading.ts                # 트레이딩 API
│   │   └── settings.ts               # 설정 API
│   ├── hooks/
│   │   ├── useAuth.ts                # 인증 훅
│   │   ├── usePositions.ts           # 포지션 훅
│   │   ├── useRealtime.ts            # 실시간 데이터 훅
│   │   └── useStrategy.ts            # 전략 설정 훅
│   ├── store/
│   │   ├── authStore.ts              # 인증 상태 (Zustand)
│   │   ├── positionStore.ts          # 포지션 상태
│   │   └── settingsStore.ts          # 설정 상태
│   └── utils/
│       ├── formatters.ts             # 데이터 포맷팅
│       └── validators.ts             # 입력 검증
├── public/
│   └── images/
├── styles/
│   └── globals.css
├── next.config.js
├── tailwind.config.ts
├── package.json
└── tsconfig.json
```

### 주요 페이지 설계

#### 1. 메인 대시보드 (`/dashboard`)
```tsx
// 기능:
// - 실시간 포지션 현황 (WebSocket)
// - 총 수익률 차트 (Recharts)
// - 최근 거래 내역
// - AI 시장 분석 요약

// UI 구성:
<DashboardLayout>
  <StatsGrid>
    <StatCard title="총 자산" value="$10,523.45" change="+5.2%" />
    <StatCard title="오늘 수익" value="$324.12" change="+3.1%" />
    <StatCard title="활성 포지션" value="3" />
    <StatCard title="승률" value="65.3%" />
  </StatsGrid>

  <PnLChart data={performanceData} />

  <ActivePositions>
    {positions.map(pos => (
      <PositionCard key={pos.id} position={pos} />
    ))}
  </ActivePositions>

  <AIInsights>
    <MarketSentiment />
    <TradingRecommendations />
  </AIInsights>
</DashboardLayout>
```

#### 2. 거래소 API 설정 (`/settings/exchanges`)
```tsx
// 기능:
// - Binance/OKX API 키 등록
// - 자동 암호화 (프론트엔드 → 백엔드 HTTPS)
// - 연결 테스트
// - IP 화이트리스트 안내

// UI 구성:
<SettingsLayout>
  <ExchangeSelector
    exchanges={["Binance", "OKX"]}
    selected={selectedExchange}
    onChange={setSelectedExchange}
  />

  <APIKeyForm onSubmit={handleSaveAPIKey}>
    <Input
      label="API Key"
      type="password"
      placeholder="Enter your API key"
      required
    />
    <Input
      label="API Secret"
      type="password"
      placeholder="Enter your API secret"
      required
    />
    <Input
      label="Passphrase (OKX only)"
      type="password"
      placeholder="Optional"
    />
    <Checkbox label="Testnet Mode" />
    <Button type="submit">Test Connection & Save</Button>
  </APIKeyForm>

  <SecurityChecklist>
    <CheckItem text="Enable IP Whitelist on exchange" />
    <CheckItem text="Disable withdrawal permissions" />
    <CheckItem text="Enable Futures trading only" />
  </SecurityChecklist>
</SettingsLayout>
```

#### 3. 전략 설정 (`/settings/strategy`)
```tsx
// 기능:
// - 투입금 비율 설정 (슬라이더)
// - 롱/숏별 익절/손절 설정
// - 레버리지 설정
// - 리스크 시뮬레이션

// UI 구성:
<SettingsLayout>
  <StrategyForm onSubmit={handleSaveStrategy}>
    <Section title="투입금 설정">
      <Slider
        label="전체 담보금 대비 투입 비율"
        min={1}
        max={100}
        value={investmentPercent}
        onChange={setInvestmentPercent}
        unit="%"
      />
      <Info>현재 담보금: $10,000 → 투입금: ${10000 * investmentPercent / 100}</Info>
    </Section>

    <Section title="롱 포지션 설정">
      <Input
        label="익절 목표 (상승률)"
        type="number"
        min={0.1}
        max={100}
        value={longTakeProfit}
        onChange={setLongTakeProfit}
        suffix="%"
      />
      <Input
        label="손절 목표 (하락률)"
        type="number"
        min={0.1}
        max={100}
        value={longStopLoss}
        onChange={setLongStopLoss}
        suffix="%"
      />
    </Section>

    <Section title="숏 포지션 설정">
      <Input
        label="익절 목표 (하락률)"
        type="number"
        min={0.1}
        max={100}
        value={shortTakeProfit}
        onChange={setShortTakeProfit}
        suffix="%"
      />
      <Input
        label="손절 목표 (상승률)"
        type="number"
        min={0.1}
        max={100}
        value={shortStopLoss}
        onChange={setShortStopLoss}
        suffix="%"
      />
    </Section>

    <Section title="레버리지 설정">
      <Slider
        label="선물 레버리지 배수"
        min={1}
        max={125}
        value={leverage}
        onChange={setLeverage}
        unit="x"
        marks={[1, 3, 5, 10, 20, 50, 100, 125]}
      />
      <Warning>
        높은 레버리지는 큰 손실 위험이 있습니다. 권장: 3x 이하
      </Warning>
    </Section>

    <RiskSimulator
      investment={investmentPercent}
      leverage={leverage}
      stopLoss={longStopLoss}
    >
      <SimulationResult>
        <p>최대 손실 금액: ${maxLoss}</p>
        <p>청산 가격: ${liquidationPrice}</p>
        <p>리스크/보상 비율: {riskRewardRatio}</p>
      </SimulationResult>
    </RiskSimulator>

    <Button type="submit">Save Strategy</Button>
  </StrategyForm>
</SettingsLayout>
```

#### 4. TradingView 인디케이터 설정 (`/settings/indicators`)
```tsx
// 기능:
// - 5개 템플릿 인디케이터 선택
// - 파라미터 커스터마이징
// - Pine Script 자동 생성
// - Webhook URL 복사

// UI 구성:
<SettingsLayout>
  <IndicatorLibrary>
    <IndicatorCard
      id="ema_crossover"
      name="EMA Crossover"
      description="빠른 EMA와 느린 EMA의 크로스오버"
      difficulty="Beginner"
      winRate={58.3}
      selected={selectedIndicator === "ema_crossover"}
      onClick={() => setSelectedIndicator("ema_crossover")}
    />
    {/* 나머지 4개 인디케이터 카드 */}
  </IndicatorLibrary>

  <ParameterCustomizer indicator={selectedIndicator}>
    <Input label="Fast EMA Length" type="number" defaultValue={9} />
    <Input label="Slow EMA Length" type="number" defaultValue={21} />
    <Input label="Leverage" type="number" defaultValue={3} />
  </ParameterCustomizer>

  <PineScriptPreview>
    <CodeBlock language="pine">{generatedPineScript}</CodeBlock>
    <Button onClick={copyToClipboard}>Copy Pine Script</Button>
  </PineScriptPreview>

  <WebhookSetup>
    <Input
      label="Webhook URL"
      value={webhookURL}
      readOnly
      suffix={<CopyButton />}
    />
    <TutorialSteps>
      <Step>1. Copy Pine Script above</Step>
      <Step>2. Open TradingView → Pine Editor → Paste</Step>
      <Step>3. Add to Chart</Step>
      <Step>4. Create Alert → Webhook URL → Paste</Step>
      <Step>5. Done! Your strategy is live.</Step>
    </TutorialSteps>
  </WebhookSetup>
</SettingsLayout>
```

---

## 보안 아키텍처

### 다층 보안 전략

#### Layer 1: 네트워크 보안
```yaml
HTTPS: Let's Encrypt SSL/TLS 인증서
HSTS: Strict-Transport-Security 헤더
CORS: 화이트리스트 기반 CORS 정책
Rate Limiting:
  - IP 기반: 60 req/min
  - 사용자 기반: 100 req/min
  - Webhook: 10 req/min
DDoS Protection: Cloudflare 또는 AWS Shield
IP Whitelist: 거래소 API 키 IP 제한
```

#### Layer 2: 애플리케이션 보안
```yaml
Authentication:
  - JWT (Access Token: 15분, Refresh Token: 7일)
  - bcrypt (비밀번호 해싱, cost factor 12)
  - 2FA: TOTP (Google Authenticator)
Authorization:
  - RBAC (Role-Based Access Control)
  - User/Admin 역할 구분
Input Validation:
  - Pydantic 모델로 모든 입력 검증
  - SQL Injection 방지 (ORM 사용)
  - XSS 방지 (입력 sanitize)
API Key Encryption:
  - AES-256-GCM (Galois/Counter Mode)
  - 사용자별 고유 키 (Key Derivation Function)
  - 환경변수 ENCRYPTION_KEY로 마스터 키 관리
HMAC Verification:
  - Webhook 서명 검증 (SHA-256)
  - Replay Attack 방지 (타임스탬프 ±5분)
```

#### Layer 3: 데이터 보안
```yaml
Encryption at Rest:
  - PostgreSQL: 민감 컬럼 암호화
  - API Keys: AES-256 암호화
  - Passwords: bcrypt 해싱
Encryption in Transit:
  - HTTPS/TLS 1.3
  - WebSocket Secure (WSS)
Data Minimization:
  - 로그에 민감 정보 기록 금지
  - API 응답에서 민감 필드 제외
Backup Security:
  - 백업 파일 암호화
  - S3 서버 사이드 암호화 (SSE-S3)
```

#### Layer 4: 모니터링 및 감사
```yaml
Audit Logging:
  - 모든 API 요청 로깅
  - 사용자 활동 추적
  - 보안 이벤트 기록
Anomaly Detection:
  - 비정상 거래 패턴 감지
  - 로그인 시도 횟수 제한
  - 의심스러운 IP 차단
Alerting:
  - 보안 이벤트 즉시 알림
  - 실패한 로그인 시도 알림
  - API 키 변경 알림
```

### 보안 체크리스트

#### 개발 환경
- [ ] `.env` 파일 `.gitignore`에 추가
- [ ] 테스트넷 API 키만 사용
- [ ] DEBUG=True, 상세 에러 로그
- [ ] HTTPS 로컬 개발 환경 (mkcert)

#### 프로덕션 환경
- [ ] DEBUG=False, 에러 상세 정보 숨김
- [ ] 강력한 SECRET_KEY 생성 (openssl rand -hex 32)
- [ ] ENCRYPTION_KEY 생성 (Fernet.generate_key())
- [ ] 2FA 필수 활성화
- [ ] Rate Limiting 활성화
- [ ] IP 화이트리스트 설정 (거래소)
- [ ] HTTPS/TLS 1.3 강제
- [ ] 정기적인 보안 패치
- [ ] 침투 테스트 수행
- [ ] 보안 감사 로그 검토

---

## 데이터베이스 설계

### ERD (Entity-Relationship Diagram)
```
┌─────────────────┐
│      Users      │
├─────────────────┤
│ id (PK)         │
│ email (UNIQUE)  │
│ password_hash   │
│ is_active       │
│ is_2fa_enabled  │
│ totp_secret     │
│ created_at      │
│ updated_at      │
└────────┬────────┘
         │ 1:N
         ↓
┌─────────────────┐
│    ApiKeys      │
├─────────────────┤
│ id (PK)         │
│ user_id (FK)    │
│ account_id      │
│ exchange        │
│ api_key_enc     │
│ api_secret_enc  │
│ passphrase_enc  │
│ testnet         │
│ created_at      │
└────────┬────────┘
         │ 1:N
         ↓
┌─────────────────┐
│   Strategies    │
├─────────────────┤
│ id (PK)         │
│ user_id (FK)    │
│ name            │
│ indicator_id    │
│ investment_pct  │ ← 전체 담보금의 몇 %
│ long_tp_pct     │ ← 롱 익절 %
│ long_sl_pct     │ ← 롱 손절 %
│ short_tp_pct    │ ← 숏 익절 %
│ short_sl_pct    │ ← 숏 손절 %
│ leverage        │ ← 레버리지 배수
│ is_active       │
│ created_at      │
│ updated_at      │
└────────┬────────┘
         │ 1:N
         ↓
┌─────────────────┐
│   Positions     │
├─────────────────┤
│ id (PK)         │
│ user_id (FK)    │
│ strategy_id (FK)│
│ exchange        │
│ symbol          │
│ side (LONG/SHORT)│
│ entry_price     │
│ quantity        │
│ leverage        │
│ stop_loss       │
│ take_profit     │
│ unrealized_pnl  │
│ realized_pnl    │
│ status (OPEN/CLOSED)│
│ opened_at       │
│ closed_at       │
└────────┬────────┘
         │ 1:N
         ↓
┌─────────────────┐
│     Orders      │
├─────────────────┤
│ id (PK)         │
│ position_id (FK)│
│ exchange        │
│ order_id        │
│ symbol          │
│ side            │
│ type            │
│ price           │
│ quantity        │
│ filled_qty      │
│ status          │
│ created_at      │
│ filled_at       │
└─────────────────┘

┌─────────────────┐
│  Performances   │
├─────────────────┤
│ id (PK)         │
│ user_id (FK)    │
│ date            │
│ total_pnl       │
│ win_rate        │
│ total_trades    │
│ roi             │
│ sharpe_ratio    │
└─────────────────┘

┌─────────────────┐
│ TelegramBots    │
├─────────────────┤
│ id (PK)         │
│ user_id (FK)    │
│ bot_token_enc   │
│ chat_id         │
│ is_active       │
│ created_at      │
└─────────────────┘
```

### 주요 테이블 스키마

#### users 테이블
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    is_2fa_enabled BOOLEAN DEFAULT FALSE,
    totp_secret VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_email ON users(email);
```

#### strategies 테이블
```sql
CREATE TABLE strategies (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    indicator_id VARCHAR(50) NOT NULL,  -- ema_crossover, rsi_reversal 등
    investment_pct DECIMAL(5, 2) DEFAULT 10.00,  -- 전체 담보금의 10%
    long_tp_pct DECIMAL(5, 2) DEFAULT 5.00,      -- 롱 익절 5%
    long_sl_pct DECIMAL(5, 2) DEFAULT 2.00,      -- 롱 손절 2%
    short_tp_pct DECIMAL(5, 2) DEFAULT 5.00,     -- 숏 익절 5%
    short_sl_pct DECIMAL(5, 2) DEFAULT 2.00,     -- 숏 손절 2%
    leverage INTEGER DEFAULT 3,                   -- 레버리지 3배
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_strategies_user_id ON strategies(user_id);
CREATE INDEX idx_strategies_is_active ON strategies(is_active);
```

#### positions 테이블
```sql
CREATE TABLE positions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    strategy_id INTEGER REFERENCES strategies(id) ON DELETE SET NULL,
    exchange VARCHAR(20) NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    side VARCHAR(10) NOT NULL,  -- LONG or SHORT
    entry_price DECIMAL(18, 8) NOT NULL,
    quantity DECIMAL(18, 8) NOT NULL,
    leverage INTEGER NOT NULL,
    stop_loss DECIMAL(18, 8),
    take_profit DECIMAL(18, 8),
    unrealized_pnl DECIMAL(18, 8) DEFAULT 0,
    realized_pnl DECIMAL(18, 8) DEFAULT 0,
    status VARCHAR(20) DEFAULT 'OPEN',  -- OPEN, CLOSED
    opened_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    closed_at TIMESTAMP
);

CREATE INDEX idx_positions_user_id ON positions(user_id);
CREATE INDEX idx_positions_status ON positions(status);
CREATE INDEX idx_positions_symbol ON positions(symbol);
```

---

## API 설계

### REST API Endpoints

#### 인증 (Authentication)
```
POST   /api/v1/auth/register            # 회원가입
POST   /api/v1/auth/login               # 로그인
POST   /api/v1/auth/logout              # 로그아웃
POST   /api/v1/auth/refresh             # 토큰 갱신
POST   /api/v1/auth/verify-2fa          # 2FA 검증
GET    /api/v1/auth/2fa/setup           # 2FA 설정 (QR 코드)
```

#### 사용자 (Users)
```
GET    /api/v1/users/me                 # 현재 사용자 정보
PUT    /api/v1/users/me                 # 사용자 정보 수정
DELETE /api/v1/users/me                 # 계정 삭제
```

#### 거래소 API 키 (Exchange API Keys)
```
POST   /api/v1/accounts/register        # API 키 등록
GET    /api/v1/accounts                 # API 키 목록
GET    /api/v1/accounts/{account_id}    # 특정 API 키 조회
PUT    /api/v1/accounts/{account_id}    # API 키 수정
DELETE /api/v1/accounts/{account_id}    # API 키 삭제
POST   /api/v1/accounts/{account_id}/test # 연결 테스트
```

#### 전략 설정 (Strategies)
```
POST   /api/v1/strategies               # 전략 생성
GET    /api/v1/strategies                # 전략 목록
GET    /api/v1/strategies/{id}          # 특정 전략 조회
PUT    /api/v1/strategies/{id}          # 전략 수정
DELETE /api/v1/strategies/{id}          # 전략 삭제
POST   /api/v1/strategies/{id}/activate # 전략 활성화
POST   /api/v1/strategies/{id}/deactivate # 전략 비활성화
```

#### 포지션 (Positions)
```
GET    /api/v1/positions                # 활성 포지션 목록
GET    /api/v1/positions/{id}           # 특정 포지션 조회
POST   /api/v1/positions/{id}/close     # 수동 포지션 청산
GET    /api/v1/positions/history        # 과거 포지션 내역
```

#### 성과 분석 (Performance)
```
GET    /api/v1/performance/summary      # 종합 성과
GET    /api/v1/performance/daily        # 일별 수익률
GET    /api/v1/performance/weekly       # 주별 수익률
GET    /api/v1/performance/monthly      # 월별 수익률
```

#### TradingView Webhook
```
POST   /api/v1/webhook/tradingview      # Webhook 수신 (기존)
```

#### 텔레그램 (Telegram)
```
POST   /api/v1/telegram/register        # 텔레그램 봇 등록
GET    /api/v1/telegram                 # 텔레그램 봇 정보
DELETE /api/v1/telegram                 # 텔레그램 봇 삭제
POST   /api/v1/telegram/test            # 테스트 알림
```

#### Pine Script (AI)
```
GET    /api/v1/pine-script/strategies   # 전략 라이브러리
POST   /api/v1/pine-script/customize    # 전략 커스터마이징
POST   /api/v1/pine-script/analyze      # Pine Script 분석
POST   /api/v1/pine-script/generate     # AI 전략 생성
```

### WebSocket Events

#### 서버 → 클라이언트
```typescript
// 실시간 포지션 업데이트
{
  event: "position_update",
  data: {
    position_id: 123,
    unrealized_pnl: 45.23,
    pnl_percentage: 2.3,
    current_price: 43250.50
  }
}

// 주문 체결 알림
{
  event: "order_filled",
  data: {
    order_id: 456,
    symbol: "BTCUSDT",
    side: "LONG",
    price: 43200.00,
    quantity: 0.05
  }
}

// AI 추천 알림
{
  event: "ai_recommendation",
  data: {
    symbol: "BTCUSDT",
    action: "CLOSE_POSITION",
    reason: "시장 급락 감지, 조기 청산 권장",
    confidence: 0.85
  }
}
```

#### 클라이언트 → 서버
```typescript
// 실시간 데이터 구독
{
  event: "subscribe",
  data: {
    channels: ["positions", "orders", "ai_signals"]
  }
}

// 구독 해제
{
  event: "unsubscribe",
  data: {
    channels: ["ai_signals"]
  }
}
```

---

## 배포 전략

### Docker Compose 구성
```yaml
version: '3.8'

services:
  # PostgreSQL 데이터베이스
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: tradingbot
      POSTGRES_USER: tradingbot
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  # Redis 캐시
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  # FastAPI 백엔드
  backend:
    build:
      context: ./trading-backend
      dockerfile: Dockerfile
    environment:
      - DATABASE_URL=postgresql://tradingbot:${DB_PASSWORD}@postgres:5432/tradingbot
      - REDIS_URL=redis://redis:6379
    ports:
      - "8001:8001"
    depends_on:
      - postgres
      - redis
    volumes:
      - ./trading-backend:/app
    command: uvicorn main:app --host 0.0.0.0 --port 8001 --reload

  # Celery Worker
  celery_worker:
    build:
      context: ./trading-backend
      dockerfile: Dockerfile
    environment:
      - DATABASE_URL=postgresql://tradingbot:${DB_PASSWORD}@postgres:5432/tradingbot
      - REDIS_URL=redis://redis:6379
    depends_on:
      - postgres
      - redis
    command: celery -A app.tasks.celery_app worker --loglevel=info

  # Next.js 프론트엔드
  frontend:
    build:
      context: ./trading-frontend
      dockerfile: Dockerfile
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:8001
    ports:
      - "3000:3000"
    depends_on:
      - backend
    volumes:
      - ./trading-frontend:/app
      - /app/node_modules
    command: npm run dev

  # Nginx 리버스 프록시
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - frontend
      - backend

volumes:
  postgres_data:
  redis_data:
```

### 프로덕션 배포 체크리스트

#### 환경 변수 설정
- [ ] `SECRET_KEY` - JWT 서명 키 (openssl rand -hex 32)
- [ ] `ENCRYPTION_KEY` - API 키 암호화 키 (Fernet.generate_key())
- [ ] `DATABASE_URL` - PostgreSQL 연결 문자열
- [ ] `REDIS_URL` - Redis 연결 문자열
- [ ] `OPENAI_API_KEY` - GPT-4 API 키
- [ ] `ANTHROPIC_API_KEY` - Claude API 키
- [ ] `SENTRY_DSN` - 에러 추적 (선택사항)

#### 데이터베이스 마이그레이션
```bash
# Alembic 마이그레이션 실행
alembic upgrade head
```

#### SSL/TLS 인증서
```bash
# Let's Encrypt 인증서 발급
certbot certonly --webroot -w /var/www/html -d yourdomain.com
```

#### 서비스 시작
```bash
# Docker Compose로 모든 서비스 시작
docker-compose up -d

# 로그 확인
docker-compose logs -f backend
docker-compose logs -f frontend
```

#### 헬스 체크
```bash
# 백엔드 헬스 체크
curl https://yourdomain.com/api/v1/health

# 프론트엔드 접근 확인
curl https://yourdomain.com
```

---

## 개발 로드맵

### Phase 1: 백엔드 핵심 기능 (2주)
- ✅ 사용자 인증 시스템 (회원가입, 로그인, 2FA)
- ✅ 거래소 API 키 관리 (암호화, 저장, 연결 테스트)
- ✅ 전략 설정 시스템 (익절/손절/레버리지)
- ✅ 리스크 관리 시스템 (포지션 사이징, 리스크 한도)
- ✅ Webhook 수신 및 주문 실행
- ✅ WebSocket 실시간 통신

### Phase 2: AI 분석 강화 (1주)
- ✅ 차트 패턴 분석 (GPT-4 + Claude)
- ✅ 거래량 프로파일 분석
- ✅ 프랙탈 현상 분석
- ✅ AI 종합 추천 시스템

### Phase 3: 프론트엔드 개발 (2주)
- ✅ Next.js 프로젝트 셋업
- ✅ 인증 페이지 (로그인, 회원가입, 2FA)
- ✅ 메인 대시보드 (실시간 포지션, 수익률)
- ✅ 설정 페이지 (거래소, 텔레그램, 인디케이터, 전략)
- ✅ 차트 및 성과 분석 페이지

### Phase 4: 통합 테스트 및 보안 강화 (1주)
- ✅ 전체 플로우 E2E 테스트
- ✅ 보안 감사 (침투 테스트)
- ✅ 성능 최적화
- ✅ 문서화 완성

### Phase 5: 배포 및 모니터링 (1주)
- ✅ 프로덕션 환경 배포
- ✅ 모니터링 시스템 구축 (Grafana, Prometheus)
- ✅ 백업 자동화
- ✅ 사용자 온보딩 가이드

---

## 참고 문서

- [README.md](README.md) - 프로젝트 개요
- [SECURITY.md](SECURITY.md) - 보안 가이드
- [PINE_SCRIPT_GUIDE.md](PINE_SCRIPT_GUIDE.md) - Pine Script AI 가이드
- [API Documentation](http://localhost:8001/docs) - Swagger UI
- [CLAUDE.md](CLAUDE.md) - Claude Code 통합 컨텍스트

---

**마지막 업데이트**: 2025-01-18
**문서 버전**: 2.0.0
**작성자**: TradingBot AI Development Team
