# 트레이딩 전략 개요

TradingBot AI가 지원하는 6가지 AI 트레이딩 전략을 알아보세요.

## 📊 전략 비교표

| 전략 | 난이도 | 승률 | 적합한 시장 | 권장 레버리지 |
|------|--------|------|-------------|---------------|
| [SuperTrend](supertrend.md) | ⭐ 쉬움 | 60-70% | 추세장 | 5-10배 |
| [RSI + EMA](rsi-ema.md) | ⭐⭐ 보통 | 55-65% | 박스권 | 3-7배 |
| [EMA Crossover](ema-crossover.md) | ⭐ 쉬움 | 50-60% | 추세장 | 5-10배 |
| [MACD + Stochastic](macd-stochastic.md) | ⭐⭐⭐ 어려움 | 55-70% | 모든 시장 | 3-7배 |
| [Bollinger Bands + RSI](bollinger-rsi.md) | ⭐⭐ 보통 | 55-65% | 변동성 큰 시장 | 3-5배 |
| [Ichimoku Cloud](ichimoku.md) | ⭐⭐⭐⭐ 매우 어려움 | 60-75% | 추세장 | 5-10배 |

## 🎯 전략 선택 가이드

### 초보자 추천

#### 1순위: SuperTrend
```
✅ 가장 단순한 로직
✅ 명확한 진입/청산 시그널
✅ 백테스팅 성과 우수
```

#### 2순위: EMA Crossover
```
✅ 이동평균 기반 (직관적)
✅ 골든/데드 크로스 (유명한 전략)
```

### 중급자 추천

#### RSI + EMA
```
✅ 과매수/과매도 필터링
✅ 추세 확인 (EMA)
✅ 박스권 거래에 유리
```

#### Bollinger Bands + RSI
```
✅ 변동성 기반
✅ 평균 회귀 전략
✅ 급등/급락 시 진입
```

### 고급자 추천

#### MACD + Stochastic
```
✅ 모멘텀 + 스토캐스틱 조합
✅ 다이버전스 활용
✅ 복합 시그널
```

#### Ichimoku Cloud
```
✅ 5가지 지표 종합
✅ 지지/저항 예측
✅ 강력한 추세 추종
```

## 📈 시장 상황별 전략

### 강한 상승 추세

```
1순위: SuperTrend (추세 추종)
2순위: Ichimoku Cloud (구름 돌파)
3순위: EMA Crossover (골든 크로스)
```

### 강한 하락 추세

```
1순위: SuperTrend (숏 포지션)
2순위: EMA Crossover (데드 크로스)
```

### 박스권 (횡보장)

```
1순위: RSI + EMA (과매수/과매도)
2순위: Bollinger Bands + RSI (밴드 터치)
```

### 변동성 큰 시장

```
1순위: Bollinger Bands + RSI
2순위: MACD + Stochastic
```

## ⚙️ 파라미터 기본 설정

### SuperTrend
```yaml
ATR Period: 10
Factor: 3.0
Timeframe: 15분 또는 1시간
```

### RSI + EMA
```yaml
RSI Length: 14
RSI Overbought: 70
RSI Oversold: 30
EMA Length: 200
Timeframe: 1시간 또는 4시간
```

### EMA Crossover
```yaml
Fast EMA: 12
Slow EMA: 26
Timeframe: 15분 또는 1시간
```

### MACD + Stochastic
```yaml
MACD Fast: 12
MACD Slow: 26
MACD Signal: 9
Stochastic K: 14
Stochastic D: 3
Timeframe: 1시간
```

### Bollinger Bands + RSI
```yaml
BB Length: 20
BB Mult: 2.0
RSI Length: 14
Timeframe: 15분 또는 1시간
```

### Ichimoku Cloud
```yaml
Conversion Line: 9
Base Line: 26
Leading Span B: 52
Displacement: 26
Timeframe: 1시간 또는 4시간
```

## 🎓 학습 경로

### 1단계: 이론 학습

```
1. 각 전략 문서 읽기
2. 지표 의미 이해
3. TradingView에서 지표 확인
```

### 2단계: 백테스팅

```
1. TradingView Strategy Tester 사용
2. 과거 1개월 데이터로 테스트
3. 승률, 손익, MDD 확인
```

### 3단계: Paper Trading

```
1. Testnet API 키 등록
2. Pine Script 작성
3. 실시간 시그널 테스트
```

### 4단계: 실전 투입

```
1. 최소 1주일 Testnet 테스트
2. 성과 검토
3. 소액 실전 시작
```

## 📊 성과 지표

### 백테스팅 결과 해석

```yaml
총 거래 수: 100회 이상 (데이터 충분성)
승률: 50% 이상 (손절/익절 비율 고려)
Profit Factor: 1.5 이상 (수익/손실 비율)
Max Drawdown: -20% 이하 (최대 손실폭)
Sharpe Ratio: 1.0 이상 (위험 대비 수익)
```

### 실전 모니터링

```
일일 체크:
- 오늘 거래 수
- 승률
- 총 손익

주간 체크:
- 주간 승률
- 최대 연속 손실
- Drawdown

월간 체크:
- 월 수익률
- 전략별 성과 비교
- 파라미터 조정 검토
```

## ⚠️ 위험 관리

### 손절/익절 비율

```
권장: 손절 2% / 익절 5% (1:2.5 비율)

예시:
- 진입가: 40,000 USDT
- 손절: 39,200 USDT (-2%)
- 익절: 42,000 USDT (+5%)
```

### 포지션 크기

```
초보: 계좌의 5-10%
중급: 계좌의 10-20%
고급: 계좌의 20-30%

⚠️ 전체 계좌를 한 번에 투입 금지!
```

### 레버리지

```
초보: 3-5배
중급: 5-10배
고급: 10-20배

⚠️ 20배 이상은 매우 위험!
```

## 📚 상세 전략 가이드

각 전략의 상세한 설명은 개별 문서를 참조하세요:

- [SuperTrend 전략](supertrend.md)
- [RSI + EMA 전략](rsi-ema.md)
- [MACD + Stochastic 전략](macd-stochastic.md)
- [Ichimoku Cloud 전략](ichimoku.md)
- [Bollinger Bands + RSI 전략](bollinger-rsi.md)
- [EMA Crossover 전략](ema-crossover.md)
