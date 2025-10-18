# 🤖 AI 기반 Pine Script 분석 및 생성 가이드

TradingView 유명 전략을 선택하거나, AI로 새로운 전략을 생성하는 완전 가이드

---

## 🎯 시스템 개요

### 핵심 기능

1. **전략 라이브러리** 📚
   - 커뮤니티 검증된 5개 유명 전략 템플릿 제공
   - Webhook 자동 통합
   - 원클릭 커스터마이징

2. **AI 분석기** 🔍
   - Pine Script 코드 파싱 및 분석
   - GPT-4 + Claude 이중 분석
   - 품질 점수 및 개선 추천

3. **AI 생성기** ✨
   - 자연어 → Pine Script 자동 생성
   - 파라미터 최적화
   - 리스크 관리 자동 추가

---

## 📚 전략 라이브러리 (5개 검증된 전략)

### 1. **EMA Crossover** (초보자 추천 ⭐⭐⭐⭐⭐)

```yaml
ID: ema_crossover
카테고리: Trend Following
난이도: Beginner
인기도: 95/100

성과 (백테스트):
  승률: 58.3%
  수익률: 1.42
  샤프비율: 1.15
  최대손실: -12.5%

전략:
  - 빠른 EMA(9)가 느린 EMA(21)를 상향 돌파 → 롱 진입
  - 빠른 EMA가 느린 EMA를 하향 돌파 → 숏 진입
  - 트렌드 시장에 최적화

파라미터:
  - fast_length: 9 (추천: 7-12)
  - slow_length: 21 (추천: 18-26)
  - leverage: 3 (추천: 1-5)
```

### 2. **RSI Mean Reversion** (초보자 추천 ⭐⭐⭐⭐)

```yaml
ID: rsi_reversal
카테고리: Mean Reversion
난이도: Beginner
인기도: 90/100

성과 (백테스트):
  승률: 62.1%
  수익률: 1.58
  샤프비율: 1.32
  최대손실: -9.8%

전략:
  - RSI가 30 이하로 하락 → 롱 진입 (과매도 반등)
  - RSI가 70 이상으로 상승 → 숏 진입 (과매수 조정)
  - 레인지 시장에 최적화

파라미터:
  - rsi_length: 14
  - oversold: 30 (추천: 25-35)
  - overbought: 70 (추천: 65-75)
  - leverage: 2 (추천: 1-3)
```

### 3. **MACD + RSI Combo** (중급자 추천 ⭐⭐⭐⭐)

```yaml
ID: macd_rsi_combo
카테고리: Trend Following
난이도: Intermediate
인기도: 87/100

성과 (백테스트):
  승률: 64.5%
  수익률: 1.72
  샤프비율: 1.48
  최대손실: -11.2%

전략:
  - MACD가 시그널선을 상향 돌파 + RSI > 50 → 롱 진입
  - MACD가 시그널선을 하향 돌파 + RSI < 50 → 숏 진입
  - RSI 필터로 거짓 신호 감소

파라미터:
  - macd_fast: 12
  - macd_slow: 26
  - macd_signal: 9
  - rsi_filter: 50
  - leverage: 3
```

### 4. **Bollinger Bands Breakout** (중급자 ⭐⭐⭐⭐)

```yaml
ID: bb_breakout
카테고리: Breakout
난이도: Intermediate
인기도: 82/100

성과 (백테스트):
  승률: 55.8%
  수익률: 1.38
  샤프비율: 1.05
  최대손실: -15.3%

전략:
  - 가격이 볼린저 상단 돌파 → 롱 진입
  - 가격이 볼린저 하단 돌파 → 숏 진입
  - 변동성 확대 구간에서 강력

파라미터:
  - bb_length: 20
  - bb_mult: 2.0
  - leverage: 4 (고위험)
```

### 5. **SuperTrend** (고급자 ⭐⭐⭐⭐⭐)

```yaml
ID: supertrend
카테고리: Trend Following
난이도: Advanced
인기도: 78/100

성과 (백테스트):
  승률: 60.2%
  수익률: 1.65
  샤프비율: 1.38
  최대손실: -13.7%

전략:
  - ATR 기반 SuperTrend 인디케이터
  - SuperTrend 색상 변경 시 진입/청산
  - 강한 트렌드에서 탁월한 성과

파라미터:
  - atr_period: 10
  - atr_multiplier: 3.0
  - leverage: 5 (고위험)
```

---

## 🚀 전략 사용 방법 (3단계)

### Step 1: 전략 목록 조회

```bash
# 모든 전략 조회
curl http://localhost:8001/api/v1/pine-script/strategies

# 초보자용 전략만 조회
curl "http://localhost:8001/api/v1/pine-script/strategies?difficulty=Beginner"

# 트렌드 추종 전략만 조회
curl "http://localhost:8001/api/v1/pine-script/strategies?category=Trend+Following"
```

**응답 예시**:
```json
[
  {
    "id": "ema_crossover",
    "name": "EMA Crossover Strategy",
    "description": "빠른 EMA와 느린 EMA의 크로스오버로 진입/청산",
    "category": "Trend Following",
    "difficulty": "Beginner",
    "popularity_score": 95,
    "indicators": ["EMA"],
    "default_parameters": {
      "fast_length": 9,
      "slow_length": 21,
      "leverage": 3
    },
    "backtest_results": {
      "win_rate": 58.3,
      "profit_factor": 1.42
    }
  }
]
```

### Step 2: 전략 커스터마이징

```bash
curl -X POST http://localhost:8001/api/v1/pine-script/customize \
  -H "Content-Type: application/json" \
  -d '{
    "strategy_id": "ema_crossover",
    "account_id": "my_binance_account",
    "webhook_secret": "your_webhook_secret_here",
    "custom_parameters": {
      "fast_length": 12,
      "slow_length": 26,
      "leverage": 5
    },
    "symbol": "BTCUSDT"
  }'
```

**응답**:
```json
{
  "strategy_id": "ema_crossover",
  "strategy_name": "EMA Crossover Strategy",
  "pine_script_code": "//@version=5\nstrategy(\"EMA Crossover\")\n...",
  "parameters": {
    "fast_length": 12,
    "slow_length": 26,
    "leverage": 5
  },
  "instructions": [
    "1. TradingView Pine Editor 열기",
    "2. 아래 코드를 복사하여 붙여넣기",
    "3. 'Add to chart' 클릭",
    "..."
  ]
}
```

### Step 3: TradingView에 적용

1. **Pine Editor 열기**
   - TradingView 차트 하단 "Pine Editor" 탭 클릭

2. **코드 붙여넣기**
   - API 응답의 `pine_script_code` 전체 복사
   - Pine Editor에 붙여넣기

3. **차트에 추가**
   - "Add to chart" 버튼 클릭
   - 차트에 전략이 표시됨

4. **백테스팅 확인**
   - Strategy Tester에서 성과 확인
   - Win Rate, Profit Factor, Sharpe Ratio 검토

5. **알림 생성**
   - 차트 우측 상단 "알림" 아이콘 클릭
   - 조건: 현재 전략명 선택, "alert() function calls only"
   - Webhook URL: `http://YOUR_SERVER:8001/api/v1/webhook/tradingview`
   - "생성" 클릭

---

## 🔍 Pine Script 분석 (AI 기반)

### 기존 전략 분석하기

```bash
curl -X POST http://localhost:8001/api/v1/pine-script/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "code": "//@version=5\nstrategy(\"My Strategy\")\n...",
    "include_ai_analysis": true
  }'
```

**AI 분석 내용**:
- ✅ 전략 정보 추출 (이름, 버전, 인디케이터)
- ✅ 진입/청산 조건 파악
- ✅ 리스크 관리 설정 확인
- ✅ GPT-4 + Claude 이중 분석
- ✅ 코드 품질 점수 (0-100)
- ✅ 강점/약점 분석
- ✅ 개선 추천사항

**응답 예시**:
```json
{
  "strategy_info": {
    "name": "My Custom Strategy",
    "version": 5,
    "indicators": ["EMA", "RSI"],
    "has_webhook": false
  },
  "ai_analysis": {
    "gpt4": {
      "quality_score": 75,
      "strengths": ["Clear entry logic", "Multiple indicators"],
      "weaknesses": ["No stop loss", "Missing webhook"]
    },
    "claude": {
      "code_quality_score": 78,
      "risks": ["No risk management", "Overfitting"]
    }
  },
  "recommendations": [
    "⚠️ Webhook 알림이 없습니다. alert() 함수를 추가하세요.",
    "⚠️ 손절매 설정이 없습니다. strategy.exit()를 추가하세요."
  ],
  "quality_score": 76.5
}
```

---

## ✨ AI 전략 생성 (실험적 기능)

### 자연어로 전략 생성하기

```bash
curl -X POST http://localhost:8001/api/v1/pine-script/generate \
  -H "Content-Type: application/json" \
  -d '{
    "description": "RSI가 30 이하일 때 롱 진입하고, 70 이상일 때 청산하는 전략을 만들어주세요. 손절매는 진입가 대비 2%로 설정해주세요.",
    "account_id": "my_account",
    "webhook_secret": "secret123",
    "risk_level": "Low",
    "preferred_indicators": ["RSI", "EMA"]
  }'
```

**AI가 자동 생성**:
- ✅ 완전한 Pine Script v5 코드
- ✅ Webhook 알림 자동 추가
- ✅ 리스크 관리 (손절/익절)
- ✅ 한글 주석 포함
- ✅ BTCUSDT 최적화

**⚠️ 주의사항**:
```
1. AI 생성 전략은 실험적 기능입니다.
2. 반드시 백테스팅을 수행하세요 (최소 6개월 데이터).
3. Testnet에서 충분히 테스트하세요 (최소 1주일).
4. 손실 가능성을 충분히 인지하세요.
```

---

## ⚙️ 파라미터 최적화 (AI 기반)

### 현재 시장에 맞게 파라미터 조정

```bash
curl -X POST http://localhost:8001/api/v1/pine-script/optimize-parameters \
  -H "Content-Type: application/json" \
  -d '{
    "strategy_id": "ema_crossover",
    "market_conditions": {
      "volatility": "High",
      "trend": "Bullish",
      "volume": "Above Average"
    }
  }'
```

**AI 분석 결과**:
```json
{
  "strategy_id": "ema_crossover",
  "original_parameters": {
    "fast_length": 9,
    "slow_length": 21,
    "leverage": 3
  },
  "optimized_parameters": {
    "fast_length": 7,
    "slow_length": 18,
    "leverage": 2
  },
  "market_conditions": {
    "volatility": "High",
    "trend": "Bullish"
  },
  "recommendation": "고변동성 시장에서는 빠른 EMA를 줄이고 레버리지를 낮추세요."
}
```

---

## 📊 API 엔드포인트 요약

| 엔드포인트 | 메서드 | 설명 |
|-----------|--------|------|
| `/api/v1/pine-script/strategies` | GET | 전략 라이브러리 목록 조회 |
| `/api/v1/pine-script/strategies/{id}` | GET | 특정 전략 상세 조회 |
| `/api/v1/pine-script/customize` | POST | 전략 커스터마이징 (Webhook 통합) |
| `/api/v1/pine-script/analyze` | POST | Pine Script 분석 (AI) |
| `/api/v1/pine-script/optimize-parameters` | POST | 파라미터 최적화 (AI) |
| `/api/v1/pine-script/generate` | POST | 전략 생성 (AI, 실험적) |

**Swagger 문서**: http://localhost:8001/docs#/🤖 AI Pine Script Generator

---

## 🎓 전략 선택 가이드

### 초보자에게 추천하는 전략

```
1위: EMA Crossover (ema_crossover)
   - 가장 기본적이고 이해하기 쉬움
   - 트렌드 시장에서 안정적
   - 승률 58%, 수익률 1.42

2위: RSI Mean Reversion (rsi_reversal)
   - RSI만 사용하여 단순함
   - 레인지 시장에서 강력
   - 승률 62%, 수익률 1.58
```

### 중급자에게 추천하는 전략

```
1위: MACD + RSI Combo (macd_rsi_combo)
   - 복합 인디케이터로 신뢰도 높음
   - 거짓 신호 필터링 우수
   - 승률 64.5%, 수익률 1.72

2위: Bollinger Bands Breakout (bb_breakout)
   - 변동성 확대 구간 포착
   - 높은 수익률 잠재력
   - 승률 55.8%, 수익률 1.38
```

### 고급자에게 추천하는 전략

```
SuperTrend (supertrend)
   - ATR 기반 동적 지지/저항
   - 강한 트렌드에서 탁월
   - 승률 60.2%, 수익률 1.65
   - 높은 레버리지 가능 (주의)
```

---

## 💡 전략 개선 팁

### 1. 필터 추가로 신뢰도 향상

```pine
// EMA Crossover에 RSI 필터 추가 예시
rsiValue = ta.rsi(close, 14)

// 롱 진입: EMA 크로스오버 + RSI > 50
longCondition = ta.crossover(fastEMA, slowEMA) and rsiValue > 50

// 숏 진입: EMA 크로스언더 + RSI < 50
shortCondition = ta.crossunder(fastEMA, slowEMA) and rsiValue < 50
```

### 2. 리스크 관리 강화

```pine
// 손절매 및 익절 추가
strategy.exit(
    "Stop Loss",
    "Long",
    stop=entry_price * 0.98,      // -2% 손절
    limit=entry_price * 1.04      // +4% 익절 (RR 1:2)
)
```

### 3. 타임프레임 최적화

```
5분봉: 단기 스캘핑 (고위험, 고빈도)
15분봉: 데이트레이딩 (중간 위험)
1시간봉: 스윙 트레이딩 (권장)
4시간봉: 포지션 트레이딩 (저위험)
일봉: 장기 투자 (최저 위험)
```

---

## 🔐 보안 및 베스트 프랙티스

### Webhook Secret 관리

```
✅ DO:
- 32자 이상 랜덤 문자열 사용
- 각 계정마다 다른 Secret 사용
- 환경변수에 저장 (절대 코드에 하드코딩 금지)

❌ DON'T:
- "123456", "secret" 같은 단순 문자열
- 여러 계정에 동일 Secret 사용
- Pine Script 공개 시 Secret 노출
```

### 백테스팅 필수사항

```
최소 백테스팅 기간: 6개월
권장 백테스팅 기간: 1년 이상
다양한 시장 상황 포함: 상승장, 하락장, 횡보장

필수 체크 지표:
- Win Rate > 50%
- Profit Factor > 1.5
- Sharpe Ratio > 1.0
- Max Drawdown < 20%
```

### 실전 적용 전 체크리스트

```
[ ] Testnet에서 1주일 이상 실시간 테스트 완료
[ ] 손절매 설정 확인
[ ] 레버리지 3배 이하로 제한
[ ] 계좌의 10% 이하로 포지션 사이즈 제한
[ ] 텔레그램 알림 설정 완료
[ ] 백테스팅 성과 검증 완료
[ ] 리스크 허용 범위 설정
```

---

## 🆘 문제 해결

### "Strategy not found" 오류

```bash
# 사용 가능한 전략 ID 확인
curl http://localhost:8001/api/v1/pine-script/strategies

# 정확한 ID 사용
# ✅ "ema_crossover"
# ❌ "EMA_Crossover", "ema-crossover"
```

### AI 분석 실패

```
원인: OpenAI/Anthropic API 키 미설정

해결:
1. .env 파일 확인
   OPENAI_API_KEY=sk-...
   ANTHROPIC_API_KEY=sk-ant-...

2. 백엔드 재시작
   python main.py
```

### 생성된 전략이 작동하지 않음

```
1. Pine Editor에서 문법 오류 확인
2. 버전 확인 (//@version=5)
3. Webhook 설정 확인 (account_id, secret)
4. 백테스팅으로 전략 검증
5. 로그 확인: tail -f logs/app.log
```

---

## 📚 추가 자료

- **전체 시스템**: [README.md](README.md)
- **BTCUSDT 빠른 시작**: [BTCUSDT_QUICKSTART.md](BTCUSDT_QUICKSTART.md)
- **텔레그램 설정**: [TELEGRAM_SETUP_GUIDE.md](TELEGRAM_SETUP_GUIDE.md)
- **보안 가이드**: [SECURITY.md](SECURITY.md)
- **API 문서**: http://localhost:8001/docs

---

**AI 기반 Pine Script 시스템으로 최적의 전략을 찾으세요!** 🤖✨

검증된 전략을 선택하거나, AI로 새로운 전략을 생성하여 자동매매를 시작하세요! 🚀
