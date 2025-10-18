# Claude Code 프로젝트 컨텍스트 시스템

이 디렉토리는 Claude Code에서 프로젝트 컨텍스트를 자동으로 로드하기 위한 설정 파일을 포함합니다.

## 📁 파일 구조

```
.claude/
└── README.md (이 파일)

프로젝트 루트/
└── CLAUDE.md  ← 핵심! 모든 문서 참조
```

## 🚀 사용 방법

### Claude Code에서 컨텍스트 로드

프로젝트 작업 시작할 때 다음 명령어 사용:

```
@CLAUDE.md를 참조해서 작업해줘
```

또는 간단하게:

```
@CLAUDE.md
```

### 자동으로 로드되는 문서 (13개)

CLAUDE.md를 참조하면 다음 모든 문서가 자동으로 컨텍스트에 포함됩니다:

#### 📚 핵심 가이드
- **README.md** - 프로젝트 전체 개요
- **BTCUSDT_QUICKSTART.md** - BTCUSDT Futures 5분 빠른 시작
- **PINE_SCRIPT_GUIDE.md** - AI 기반 Pine Script 분석/생성 가이드

#### 🔧 통합 가이드
- **TELEGRAM_SETUP_GUIDE.md** - 텔레그램 알림 설정 (3분)
- **TRADINGVIEW_GUIDE.md** - TradingView 통합 가이드
- **TRADINGVIEW_WEBHOOK_GUIDE.md** - Webhook 상세 가이드

#### 🔐 보안 및 운영
- **SECURITY.md** - 보안 체크리스트 및 베스트 프랙티스

#### 📖 개발자 문서
- **USAGE_GUIDE.md** - 사용 방법 가이드
- **IMPLEMENTATION_SUMMARY.md** - 구현 요약
- **FRONTEND_INTEGRATION.md** - 프론트엔드 통합
- **PERFORMANCE_GUIDE.md** - 성능 최적화
- **OPTIMIZATION_GUIDE.md** - 파라미터 최적화
- **SYSTEM_COMPLETE.md** - 시스템 완성도 체크리스트

## 💡 활용 예시

### 1. 새로운 기능 개발

```
@CLAUDE.md

텔레그램 알림에 포지션 손익률 그래프를 추가하고 싶어요.
현재 시스템을 참고해서 구현해주세요.
```

→ Claude Code가 자동으로:
- TELEGRAM_SETUP_GUIDE.md에서 현재 알림 구조 파악
- app/services/telegram_service.py 코드 확인
- 기존 스타일 유지하며 새 기능 추가

### 2. 버그 수정

```
@CLAUDE.md

Webhook 수신은 되는데 주문이 실행되지 않아요.
로그를 확인하고 문제를 찾아주세요.
```

→ Claude Code가 자동으로:
- SECURITY.md에서 보안 검증 로직 확인
- TRADINGVIEW_WEBHOOK_GUIDE.md에서 Webhook 플로우 파악
- app/api/v1/webhook.py 디버깅

### 3. 문서 업데이트

```
@CLAUDE.md

새로 추가한 Pine Script 전략을 문서에 반영해주세요.
```

→ Claude Code가 자동으로:
- PINE_SCRIPT_GUIDE.md 구조 파악
- 기존 전략 설명 스타일 유지
- 새 전략 추가 및 문서 업데이트

## 📊 컨텍스트 범위

### 자동으로 포함되는 정보

✅ **시스템 아키텍처**: TradingView → Backend → Binance/OKX
✅ **API 엔드포인트**: 모든 REST API 정보
✅ **데이터베이스 모델**: ApiKey, Strategy 등
✅ **환경 설정**: .env 파라미터
✅ **보안 정책**: 암호화, 검증 로직
✅ **Pine Script 전략**: 5개 검증된 전략
✅ **AI 시스템**: GPT-4 + Claude 분석 로직
✅ **텔레그램 알림**: 4가지 알림 타입
✅ **에러 처리**: 커스텀 예외 계층
✅ **로깅 시스템**: 구조화된 JSON 로그

### 컨텍스트에서 제외되는 정보

❌ 실제 API 키 값 (.env 파일)
❌ 데이터베이스 비밀번호
❌ Webhook Secret
❌ 사용자 개인정보

## 🎯 베스트 프랙티스

### DO ✅

```
# 작업 시작 시 CLAUDE.md 참조
@CLAUDE.md

# 구체적인 작업 지시
텔레그램 알림에 차트 이미지를 추가해주세요.
현재 시스템 구조를 유지하면서 구현해주세요.
```

### DON'T ❌

```
# 컨텍스트 없이 작업 시작 (비추천)
텔레그램 알림 기능을 만들어주세요.
→ Claude Code가 기존 시스템을 모르므로 중복 코드 생성 가능
```

## 🔄 문서 업데이트

새로운 MD 파일을 추가했다면 CLAUDE.md를 업데이트하세요:

1. 새 MD 파일 생성
2. CLAUDE.md 열기
3. `## 📚 핵심 문서 참조` 섹션에 `@새파일.md` 추가
4. 저장

예시:
```markdown
## 📚 핵심 문서 참조

...
@NEW_FEATURE_GUIDE.md  ← 새로 추가
```

## 📝 CLAUDE.md 구조

```markdown
# TradingBot AI - Claude Code 프로젝트 컨텍스트

## 📚 핵심 문서 참조
@README.md
@BTCUSDT_QUICKSTART.md
...

## 🎯 프로젝트 개요
- 시스템 아키텍처
- 핵심 기능
- 기술 스택

## 📁 프로젝트 구조
- 디렉토리 구조
- 주요 파일 설명

## 🔑 주요 API 엔드포인트
- Webhook & Trading
- Telegram
- Pine Script (AI)

## 🔧 환경 설정
- 필수 환경변수
- .env 예시

... (기타 핵심 정보)
```

## 🎉 이점

### 1. 일관성 유지
모든 작업이 기존 시스템 구조를 따릅니다.

### 2. 시간 절약
매번 문서를 수동으로 읽을 필요가 없습니다.

### 3. 컨텍스트 연속성
작업 세션 간 컨텍스트가 유지됩니다.

### 4. 에러 감소
기존 시스템을 고려하여 코드를 생성합니다.

### 5. 문서 동기화
문서가 자동으로 최신 상태를 반영합니다.

---

**@CLAUDE.md 하나로 모든 프로젝트 정보를 활용하세요!** 🚀
