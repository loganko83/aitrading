# GitBook 설정 가이드

TradingBot AI 문서를 GitBook과 연동하는 방법입니다.

## 📋 현재 문서 구조

```
/docs
├── README.md                        # 메인 소개 페이지
├── SUMMARY.md                       # 목차 (GitBook 필수)
├── getting-started/
│   └── quick-start.md              # 5분 빠른 시작 가이드
├── guides/
│   ├── api-keys.md                 # API 키 등록 가이드
│   ├── trading-config.md           # Trading Config 설정
│   ├── webhook-setup.md            # Webhook 상세 가이드
│   ├── tradingview-integration.md  # TradingView Pine Script
│   └── strategy-selection.md       # 전략 선택 가이드
├── strategies/
│   ├── overview.md                 # 전략 개요 및 비교
│   ├── supertrend.md              # SuperTrend 전략
│   ├── rsi-ema.md                 # RSI + EMA 전략
│   └── ... (기타 전략)
├── security/
│   ├── best-practices.md          # 보안 모범 사례
│   ├── encryption.md              # AES-256 암호화
│   └── two-factor-auth.md         # 2FA 설정
├── troubleshooting/
│   ├── faq.md                     # 자주 묻는 질문
│   ├── common-issues.md           # 일반적인 문제
│   └── error-codes.md             # 에러 코드 참조
└── api-reference/
    ├── authentication.md           # API 인증
    ├── endpoints.md                # API 엔드포인트
    └── webhook-api.md              # Webhook API 상세
```

## 🚀 GitBook 연동 방법

### 1단계: GitBook 계정 생성

1. [GitBook.com](https://www.gitbook.com/) 접속
2. GitHub 계정으로 Sign Up
3. Free 플랜 선택 (Public documentation)

### 2단계: GitHub 저장소 연결

```
GitBook Dashboard → New Space → Import from GitHub

1. GitHub 저장소 선택
2. Branch: master 선택
3. Root directory: /docs (또는 루트)
4. Sync 활성화
```

### 3단계: GitBook 설정 확인

`.gitbook.yaml` 파일이 루트에 있어야 합니다:

```yaml
root: ./docs/

structure:
  readme: README.md
  summary: SUMMARY.md
```

### 4단계: SUMMARY.md 구조

GitBook은 SUMMARY.md를 읽어 좌측 메뉴를 생성합니다:

```markdown
# Table of contents

* [소개](README.md)

## 시작하기

* [빠른 시작 가이드](getting-started/quick-start.md)
* [설치 및 설정](getting-started/installation.md)

## 사용 가이드

* [API 키 등록](guides/api-keys.md)
* [Webhook 설정](guides/webhook-setup.md)

## 트레이딩 전략

* [전략 개요](strategies/overview.md)
```

### 5단계: 자동 동기화

GitHub에 push하면 자동으로 GitBook이 업데이트됩니다:

```bash
# 문서 수정
vim docs/guides/new-guide.md

# Git commit
git add docs/
git commit -m "docs: Add new guide"
git push origin master

# GitBook이 자동으로 감지하고 빌드 (1-2분 소요)
```

## 📖 GitBook 메뉴 구조

### 현재 메뉴 구조 (SUMMARY.md 기준)

```
📘 TradingBot AI
├─ 📂 시작하기
│  ├─ 빠른 시작 가이드
│  ├─ 설치 및 설정
│  └─ 첫 거래 실행
│
├─ 📂 사용 가이드
│  ├─ API 키 등록
│  ├─ Trading Config 설정
│  ├─ Webhook 설정
│  ├─ TradingView 통합
│  ├─ 전략 선택 가이드
│  └─ 대시보드 사용법
│
├─ 📂 트레이딩 전략
│  ├─ 전략 개요
│  ├─ SuperTrend 전략
│  ├─ RSI + EMA 전략
│  ├─ MACD + Stochastic 전략
│  ├─ Ichimoku Cloud 전략
│  ├─ Bollinger Bands + RSI 전략
│  └─ EMA Crossover 전략
│
├─ 📂 보안
│  ├─ 암호화 시스템
│  ├─ 보안 모범 사례
│  └─ 2단계 인증 (2FA)
│
├─ 📂 문제 해결
│  ├─ 자주 묻는 질문 (FAQ)
│  ├─ 일반적인 문제
│  └─ 에러 코드 참조
│
├─ 📂 API 참조
│  ├─ 인증
│  ├─ 엔드포인트
│  └─ Webhook API
│
└─ 📂 고급 주제
   ├─ 백테스팅 가이드
   ├─ 파라미터 최적화
   ├─ 리스크 관리
   └─ 포트폴리오 관리
```

## 🎨 GitBook 커스터마이징

### Space Settings

```
GitBook Dashboard → Space Settings

- Name: TradingBot AI
- Description: AI 기반 암호화폐 자동매매 시스템
- Logo: 로고 이미지 업로드
- Favicon: 파비콘 업로드
- Primary color: #3B82F6 (파란색)
```

### Social Links

```
Settings → Integrations

- GitHub: https://github.com/your-repo/tradingbot
- Discord: Discord 초대 링크
- Twitter: @TradingBotAI
```

## 📱 공개 URL

GitBook 빌드 완료 후:

```
Public URL: https://your-org.gitbook.io/tradingbot-ai
또는
Custom Domain: https://docs.tradingbot.ai (유료)
```

## ✅ 체크리스트

문서 배포 전 확인사항:

### 필수

- [ ] `.gitbook.yaml` 파일 존재
- [ ] `docs/README.md` 존재
- [ ] `docs/SUMMARY.md` 존재
- [ ] 모든 링크가 올바른지 확인
- [ ] 코드 예시 테스트 완료

### 권장

- [ ] 스크린샷 추가
- [ ] 동영상 튜토리얼 링크
- [ ] 검색 키워드 최적화
- [ ] 다국어 지원 (영어 추가)

## 🔄 문서 업데이트 프로세스

### 일반 업데이트

```bash
# 1. 문서 수정
vim docs/guides/webhook-setup.md

# 2. Git commit
git add docs/guides/webhook-setup.md
git commit -m "docs: Update webhook setup guide"

# 3. Push to GitHub
git push origin master

# 4. GitBook 자동 빌드 (1-2분)
```

### 대규모 업데이트

```bash
# 1. 새 브랜치 생성
git checkout -b docs/major-update

# 2. 문서 작업
# ...

# 3. Commit and push
git add docs/
git commit -m "docs: Major documentation update"
git push origin docs/major-update

# 4. GitHub Pull Request
# 5. 리뷰 후 merge
# 6. GitBook 자동 업데이트
```

## 🚀 다음 단계

### 추가 문서 작성

```
TODO:
- [ ] installation.md (상세 설치 가이드)
- [ ] first-trade.md (첫 거래 튜토리얼)
- [ ] trading-config.md (Trading Config 상세)
- [ ] strategy-selection.md (전략 선택 가이드)
- [ ] dashboard.md (대시보드 사용법)
- [ ] supertrend.md (SuperTrend 전략 상세)
- [ ] common-issues.md (일반적인 문제)
- [ ] error-codes.md (에러 코드 참조)
- [ ] encryption.md (암호화 시스템)
- [ ] two-factor-auth.md (2FA)
- [ ] authentication.md (API 인증)
- [ ] endpoints.md (API 엔드포인트)
- [ ] webhook-api.md (Webhook API 상세)
- [ ] backtesting.md (백테스팅)
- [ ] optimization.md (최적화)
- [ ] risk-management.md (리스크 관리)
- [ ] portfolio.md (포트폴리오)
```

### 다국어 지원

```
docs/
├── en/              # 영어
│   ├── README.md
│   └── ...
└── ko/              # 한국어 (현재)
    ├── README.md
    └── ...
```

### 검색 최적화

각 문서에 메타데이터 추가:

```markdown
---
description: TradingBot AI 빠른 시작 가이드 - 5분 안에 시작하기
---

# 빠른 시작 가이드
...
```

## 📞 문의

GitBook 설정 관련 문의:
- GitHub Issues
- Discord 커뮤니티
- 이메일: support@tradingbot.ai
