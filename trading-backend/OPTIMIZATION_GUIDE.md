# 자동 파라미터 최적화 시스템 가이드

## 📋 목차

1. [개요](#개요)
2. [최적화 알고리즘](#최적화-알고리즘)
3. [목적 함수](#목적-함수)
4. [API 사용법](#api-사용법)
5. [고급 기능](#고급-기능)
6. [베스트 프랙티스](#베스트-프랙티스)
7. [문제 해결](#문제-해결)

---

## 개요

**자동 파라미터 최적화 시스템**은 전략의 최적 파라미터를 자동으로 찾아줍니다.

### 핵심 기능

- ✅ **Grid Search**: 전수 조사 방식 (확실한 최적해)
- ✅ **Genetic Algorithm**: 유전 알고리즘 (빠르고 효율적)
- ✅ **Random Search**: 랜덤 탐색 (빠른 테스트)
- ✅ **Walk-Forward 검증**: 과적합 방지
- ✅ **견고성 점수**: 파라미터 안정성 평가
- ✅ **자동 과적합 탐지**: 신뢰성 확보

### 사용 시나리오

1. **새 전략 개발**: 최적 파라미터 발견
2. **기존 전략 개선**: 더 나은 파라미터 탐색
3. **시장 적응**: 시장 변화에 따른 파라미터 조정
4. **백테스트 검증**: 파라미터 민감도 분석

---

## 최적화 알고리즘

### 1. Grid Search (그리드 탐색)

**원리**: 모든 파라미터 조합을 체계적으로 테스트

**장점:**
- ✅ 확실한 최적해 보장 (탐색 공간 내)
- ✅ 간단하고 이해하기 쉬움
- ✅ 재현 가능성 높음

**단점:**
- ❌ 파라미터가 많으면 매우 느림
- ❌ 계산량 = (파라미터1 범위) × (파라미터2 범위) × ...

**추천 사용:**
- 파라미터 2-3개 이하
- 정확도가 중요한 경우
- 전략이 단순한 경우

**예시:**
```python
# SuperTrend 전략 (파라미터 2개)
period: 5, 6, 7, ..., 20  # 16개 값
multiplier: 1.0, 1.5, 2.0, ..., 5.0  # 9개 값
# 총 조합: 16 × 9 = 144개 (약 3-5분)
```

---

### 2. Genetic Algorithm (유전 알고리즘)

**원리**: 생물 진화 모방 - 선택, 교배, 돌연변이

**장점:**
- ✅ 빠름 (Grid Search 대비 90% 감소)
- ✅ 다수 파라미터 처리 가능
- ✅ 효율적 탐색

**단점:**
- ❌ 국소 최적해 가능성
- ❌ 재현성 낮음 (확률적)

**추천 사용:**
- 파라미터 4개 이상
- 속도가 중요한 경우
- 복잡한 전략

**핵심 개념:**

```
세대 1: 랜덤 50개 파라미터 조합 생성
     ↓ (백테스트로 점수 평가)
세대 2: 상위 10개 선택 → 교배 → 돌연변이
     ↓ (새로운 50개 조합 생성)
세대 3: 반복...
     ↓
세대 N: 최적 파라미터 발견
```

**파라미터:**
- `population_size`: 세대당 개체 수 (기본 50)
- `mutation_rate`: 돌연변이 확률 (기본 0.1)
- `crossover_rate`: 교배 확률 (기본 0.7)
- `elite_size`: 무조건 생존하는 상위 개체 수 (기본 5)

---

### 3. Random Search (랜덤 탐색)

**원리**: 무작위로 파라미터 샘플링

**장점:**
- ✅ 매우 빠름
- ✅ 구현 간단
- ✅ 초기 탐색에 유용

**단점:**
- ❌ 정확도 낮음
- ❌ 체계적이지 않음

**추천 사용:**
- 빠른 프로토타이핑
- 대략적인 범위 파악
- 시간 제약이 있는 경우

---

### 알고리즘 비교

| 특성 | Grid Search | Genetic Algorithm | Random Search |
|------|-------------|-------------------|---------------|
| **정확도** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| **속도** | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **파라미터 수** | 2-3개 | 4개 이상 | 제한 없음 |
| **재현성** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ |
| **계산량** | O(n^p) | O(g×m) | O(n) |

- n: 파라미터당 탐색 값 개수
- p: 파라미터 개수
- g: 세대 수
- m: 개체 수

---

## 목적 함수

### 1. Maximize Return (수익률 최대화)

**목표**: 총 수익률 %를 최대화

**특징:**
- 가장 직관적
- 리스크 고려 안함
- 높은 변동성 가능

**추천:**
- 공격적 전략
- 리스크 감수 가능한 경우

**예시 결과:**
```
수익률: +45.2%
최대 낙폭: -23.5%  # 높을 수 있음
샤프 비율: 1.2
```

---

### 2. Maximize Sharpe (샤프 비율 최대화) ⭐ 권장

**목표**: 샤프 비율 = (수익 - 무위험 수익) / 변동성

**특징:**
- 리스크 대비 수익 균형
- 안정적인 수익 추구
- 가장 널리 사용

**추천:**
- **대부분의 경우 (권장)**
- 안정적 수익 선호
- 장기 투자

**예시 결과:**
```
수익률: +32.8%
최대 낙폭: -12.3%  # 낮음
샤프 비율: 2.1  # 높음 (좋음)
```

---

### 3. Minimize Drawdown (낙폭 최소화)

**목표**: 최대 낙폭을 최소화

**특징:**
- 안정성 최우선
- 수익률 희생 가능
- 심리적 안정

**추천:**
- 보수적 투자자
- 손실 민감한 경우
- 안정성 중시

**예시 결과:**
```
수익률: +18.5%  # 낮을 수 있음
최대 낙폭: -5.2%  # 매우 낮음
샤프 비율: 1.5
```

---

### 4. Maximize Win Rate (승률 최대화)

**목표**: 승률 %를 최대화

**특징:**
- 심리적 만족감
- 수익 크기 고려 안함
- "작은 손실, 큰 수익" 전략 불리

**추천:**
- 높은 승률 선호
- 심리적 안정 중시

**예시 결과:**
```
승률: 72.5%  # 높음
수익률: +25.3%
평균 수익/손실: 1.2:1  # 낮을 수 있음
```

---

### 목적 함수 선택 가이드

```
목표가 무엇인가요?

├─ 최고 수익률!
│   → maximize_return
│
├─ 안정적이면서 수익도 원해!
│   → maximize_sharpe ⭐ 권장
│
├─ 절대 큰 손실 피하고 싶어!
│   → minimize_drawdown
│
└─ 승률 높은 전략 원해!
    → maximize_win_rate
```

---

## API 사용법

### 기본 사용법

**1. 간단한 최적화 (기본 설정)**

```bash
POST /api/v1/optimize/optimize
Content-Type: application/json

{
    "strategy_type": "supertrend",
    "method": "grid_search",
    "objective": "maximize_sharpe",
    "symbol": "BTCUSDT",
    "days_back": 90,
    "initial_capital": 10000
}
```

**응답:**
```json
{
    "success": true,
    "best_parameters": {
        "period": 12,
        "multiplier": 3.0
    },
    "best_score": 1.85,
    "objective_type": "maximize_sharpe",
    "robustness_score": 78.5,
    "is_overfit": false,
    "total_iterations": 144,
    "optimization_time_seconds": 42.3,
    "top_results": [
        {"parameters": {"period": 12, "multiplier": 3.0}, "score": 1.85},
        {"parameters": {"period": 11, "multiplier": 3.5}, "score": 1.82},
        {"parameters": {"period": 13, "multiplier": 2.5}, "score": 1.79}
    ],
    "recommendations": [
        "✅ 높은 견고성: 파라미터가 안정적으로 작동합니다."
    ]
}
```

---

### 2. 커스텀 파라미터 범위

```bash
POST /api/v1/optimize/optimize
Content-Type: application/json

{
    "strategy_type": "rsi_ema",
    "method": "genetic",
    "objective": "maximize_return",
    "symbol": "ETHUSDT",
    "days_back": 120,
    "initial_capital": 50000,
    "max_iterations": 100,
    "parameter_ranges": [
        {
            "name": "rsi_period",
            "min_value": 10,
            "max_value": 20,
            "step": 2,
            "param_type": "int"
        },
        {
            "name": "rsi_overbought",
            "min_value": 70,
            "max_value": 85,
            "step": 5,
            "param_type": "int"
        },
        {
            "name": "rsi_oversold",
            "min_value": 15,
            "max_value": 30,
            "step": 5,
            "param_type": "int"
        }
    ]
}
```

---

### 3. 유전 알고리즘 고급 설정

```bash
POST /api/v1/optimize/optimize
Content-Type: application/json

{
    "strategy_type": "macd_stoch",
    "method": "genetic",
    "objective": "maximize_sharpe",
    "symbol": "BTCUSDT",
    "days_back": 180,
    "max_iterations": 200,
    "population_size": 100,
    "mutation_rate": 0.15
}
```

---

### 4. 최적화 프리셋 조회

```bash
GET /api/v1/optimize/optimize/presets

# 응답: 전략별 추천 설정 반환
```

---

## 고급 기능

### 1. Walk-Forward 검증

**목적**: 과적합 방지

**작동 원리:**
```
전체 데이터를 학습/검증으로 분할

├─ 학습 데이터 (70%): 파라미터 최적화
│   └─ 2024-01-01 ~ 2024-09-01
│
└─ 검증 데이터 (30%): 성능 확인
    └─ 2024-09-02 ~ 2024-12-31

검증 점수가 학습 점수와 유사하면 OK!
검증 점수가 20% 이상 낮으면 과적합 의심
```

**자동 활성화**: 기본값 `enable_walk_forward: true`

---

### 2. 견고성 점수 (Robustness Score)

**계산 공식:**
```python
consistency = 1 - |train_score - validation_score| / train_score
stability = 1 - std(walk_forward_scores) / mean(walk_forward_scores)

robustness_score = (consistency + stability) / 2 × 100
```

**해석:**
- **0-50점**: 낮음 - 파라미터 불안정, 재검토 필요
- **50-70점**: 보통 - 사용 가능하나 주의 필요
- **70-85점**: 좋음 - 안정적으로 작동
- **85-100점**: 매우 좋음 - 신뢰할 수 있음

---

### 3. 과적합 탐지

**자동 판단 기준:**

1. **검증 점수 < 학습 점수 × 0.8**
   ```
   학습: 45% 수익
   검증: 30% 수익  # 20% 이상 하락 → 과적합!
   ```

2. **Walk-Forward 점수 변동성 > 평균 × 0.5**
   ```
   Window 1: 40%
   Window 2: 15%  # 큰 변동
   Window 3: 38%
   → 불안정 → 과적합 가능성
   ```

**대응 방법:**
- 더 긴 기간 데이터로 재검증
- 파라미터 범위 축소
- 단순한 전략 사용

---

### 4. Top Results 분석

**사용법:**
```json
"top_results": [
    {"parameters": {"period": 12, "multiplier": 3.0}, "score": 1.85},
    {"parameters": {"period": 11, "multiplier": 3.5}, "score": 1.82},
    {"parameters": {"period": 13, "multiplier": 2.5}, "score": 1.79}
]
```

**분석 포인트:**
- 상위 결과들의 파라미터가 유사한가?
  - **유사**: 안정적 영역 발견 ✅
  - **분산**: 파라미터 민감도 높음 ⚠️

- 점수 차이가 작은가?
  - **작음**: 여러 선택지 가능 ✅
  - **큼**: 최적 파라미터 명확 ✅

---

## 베스트 프랙티스

### 1. 데이터 기간 선택

**최소 권장 기간:**
- Grid Search: 60일 이상
- Genetic Algorithm: 90일 이상
- Walk-Forward: 120일 이상

**이유:**
- 충분한 거래 샘플 필요 (최소 30회 이상)
- 다양한 시장 상황 포함
- 과적합 방지

---

### 2. 파라미터 범위 설정

**원칙:**
- 너무 넓으면: 계산량 증가, 불안정한 파라미터 포함
- 너무 좁으면: 최적해 놓칠 가능성

**추천 방법:**
1. 먼저 넓은 범위로 Random Search
2. 좋은 영역 파악
3. 해당 영역을 Grid Search로 정밀 탐색

**예시:**
```python
# 1차: 넓은 범위 (Random Search)
period: 5 ~ 30 (모든 값)

# 결과: period 10-15가 좋음

# 2차: 좁은 범위 (Grid Search)
period: 10, 11, 12, 13, 14, 15
```

---

### 3. 목적 함수 선택 전략

**시장 상황별:**
- **상승장**: maximize_return (공격적)
- **횡보장**: maximize_sharpe (균형)
- **하락장**: minimize_drawdown (방어적)

**투자자 성향별:**
- **공격적**: maximize_return
- **균형**: maximize_sharpe ⭐
- **보수적**: minimize_drawdown

**전략 특성별:**
- **고빈도 매매**: maximize_win_rate
- **추세 추종**: maximize_return
- **평균 회귀**: maximize_sharpe

---

### 4. 최적화 주기

**권장 주기:**
- **분기마다** (3개월): 시장 변화 반영
- **시장 급변 시**: 즉시 재최적화
- **성과 저하 시**: 파라미터 재조정

**주의사항:**
- 과도한 최적화는 오히려 역효과
- "과거 맞추기"가 아닌 "미래 예측"이 목표

---

## 문제 해결

### Q1: 최적화가 너무 오래 걸립니다

**원인:**
- 파라미터 조합이 너무 많음
- Grid Search 사용

**해결:**
1. Genetic Algorithm 사용
2. 파라미터 범위 축소
3. `max_iterations` 줄이기
4. 병렬 처리 활성화

**예시:**
```json
// 변경 전 (Grid Search, 10,000개 조합)
{
    "method": "grid_search",
    "parameter_ranges": [
        {"name": "period", "min": 5, "max": 50, "step": 1},
        {"name": "multiplier", "min": 1.0, "max": 10.0, "step": 0.1}
    ]
}

// 변경 후 (Genetic, 100회 반복)
{
    "method": "genetic",
    "max_iterations": 100,
    "population_size": 50
}
```

---

### Q2: 과적합이 계속 발생합니다

**증상:**
```json
{
    "train_score": 45.2,
    "validation_score": 22.1,  // 매우 낮음
    "is_overfit": true
}
```

**원인:**
- 데이터 기간이 짧음
- 파라미터가 너무 많음
- 과도한 최적화

**해결:**
1. **더 긴 데이터 사용**
   ```json
   "days_back": 180  // 90 → 180
   ```

2. **단순한 전략 사용**
   - 파라미터 2-3개 이하
   - SuperTrend 같은 단순한 전략

3. **Walk-Forward 창 늘리기**
   ```json
   "walk_forward_windows": 5  // 기본 3 → 5
   ```

4. **목적 함수 변경**
   ```json
   "objective": "maximize_sharpe"  // 수익률보다 안정성
   ```

---

### Q3: 견고성 점수가 낮습니다

**증상:**
```json
{
    "robustness_score": 35.2,  // < 50
    "recommendations": [
        "⚠️ 낮은 견고성: Walk-Forward 점수가 불안정합니다."
    ]
}
```

**원인:**
- 파라미터가 시장 변화에 민감
- 특정 기간에만 잘 작동

**해결:**
1. **파라미터 범위 축소**
   - 극단적인 값 제외
   - 중간 범위에 집중

2. **다른 목적 함수 시도**
   ```json
   "objective": "maximize_sharpe"  // 더 안정적
   ```

3. **더 긴 기간 테스트**
   ```json
   "days_back": 365  // 1년 데이터
   ```

---

### Q4: 최적 파라미터가 매번 다릅니다

**증상:**
- 같은 설정으로 최적화해도 결과가 다름

**원인:**
- Genetic Algorithm 사용 (확률적)
- Random Search 사용

**해결:**
1. **Grid Search 사용** (재현 가능)
   ```json
   "method": "grid_search"
   ```

2. **시드 고정** (향후 지원 예정)

3. **여러 번 실행 후 평균**
   - 5-10회 실행
   - 공통적으로 나타나는 파라미터 선택

---

## 실전 예제

### 예제 1: SuperTrend 전략 최적화

**목표**: 샤프 비율 최대화

```bash
POST /api/v1/optimize/optimize
Content-Type: application/json

{
    "strategy_type": "supertrend",
    "method": "grid_search",
    "objective": "maximize_sharpe",
    "symbol": "BTCUSDT",
    "days_back": 120,
    "initial_capital": 10000,
    "max_iterations": 100
}
```

**결과 해석:**
```json
{
    "best_parameters": {
        "period": 12,
        "multiplier": 3.0
    },
    "best_score": 1.85,  // 샤프 비율
    "robustness_score": 78.5,  // 좋음
    "is_overfit": false,  // 문제 없음
    "top_results": [
        {"parameters": {"period": 12, "multiplier": 3.0}, "score": 1.85},
        {"parameters": {"period": 11, "multiplier": 3.0}, "score": 1.82},
        {"parameters": {"period": 13, "multiplier": 3.0}, "score": 1.79}
    ]
}
```

**분석:**
- ✅ 견고성 78.5점: 안정적
- ✅ 과적합 아님: 신뢰 가능
- ✅ 상위 결과 유사: period 11-13, multiplier 3.0 영역이 최적

**실전 적용:**
- **기본값**: period=12, multiplier=3.0
- **대안**: period=11 또는 13도 유사한 성과

---

### 예제 2: RSI+EMA 전략 최적화 (유전 알고리즘)

**목표**: 수익률 최대화 (빠른 최적화)

```bash
POST /api/v1/optimize/optimize
Content-Type: application/json

{
    "strategy_type": "rsi_ema",
    "method": "genetic",
    "objective": "maximize_return",
    "symbol": "ETHUSDT",
    "days_back": 180,
    "initial_capital": 50000,
    "max_iterations": 150,
    "population_size": 80,
    "mutation_rate": 0.12
}
```

**결과 해석:**
```json
{
    "best_parameters": {
        "rsi_period": 14,
        "rsi_overbought": 70,
        "rsi_oversold": 30,
        "ema_fast": 10,
        "ema_slow": 30
    },
    "best_score": 52.3,  // 52.3% 수익
    "robustness_score": 65.2,  // 보통
    "is_overfit": false,
    "optimization_time_seconds": 98.5
}
```

**분석:**
- ✅ 빠른 최적화: 98.5초 (Grid Search 대비 90% 단축)
- ⚠️ 견고성 65.2점: 보통, 추가 검증 권장
- ✅ 과적합 아님

**실전 적용:**
- 먼저 실계좌 소액으로 테스트
- 1-2주 모니터링 후 본격 사용

---

## 요약

**최적화 워크플로우:**
```
1. 전략 선택 (supertrend, rsi_ema, macd_stoch)
   ↓
2. 목적 함수 결정 (maximize_sharpe 권장)
   ↓
3. 데이터 기간 설정 (90-180일)
   ↓
4. 최적화 방법 선택
   - 파라미터 2-3개 → Grid Search
   - 파라미터 4개 이상 → Genetic Algorithm
   ↓
5. 최적화 실행
   ↓
6. 결과 검증
   - 견고성 점수 > 70
   - 과적합 여부 확인
   - Top 결과 유사성
   ↓
7. 실전 적용 (소액 테스트)
```

**핵심 체크리스트:**
- [ ] 충분한 데이터 기간 (90일 이상)
- [ ] 적절한 목적 함수 (maximize_sharpe 권장)
- [ ] 적절한 최적화 방법 (파라미터 수 고려)
- [ ] Walk-Forward 검증 활성화
- [ ] 견고성 점수 확인 (> 70 권장)
- [ ] 과적합 여부 확인
- [ ] 실전 전 소액 테스트

**문의 및 지원:**
- API 문서: `/docs`
- 프리셋 조회: `GET /api/v1/optimize/optimize/presets`
- 성능 모니터링: `GET /api/v1/performance/performance/summary`
