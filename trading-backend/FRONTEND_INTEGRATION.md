# 프론트엔드 통합 가이드

## 🚀 3단계로 완성하는 트레이딩 봇 UI

이 가이드는 **프론트엔드 개발자**가 **최소 코드**로 트레이딩 봇 UI를 구축할 수 있도록 작성되었습니다.

---

## 📋 전체 흐름

```
1. 사용자 정보 입력
   ↓
2. AI 추천 받기 (선택사항)
   ↓
3. 프리셋 선택
   ↓
4. 원클릭 백테스트 실행
   ↓
5. 결과 표시
```

---

## 🎨 React 컴포넌트 예제

### 1. API 클라이언트 설정

```typescript
// src/api/tradingApi.ts

const API_BASE = 'http://localhost:8001/api/v1';

export interface PresetInfo {
  id: string;
  name: string;
  name_ko: string;
  description_ko: string;
  category: string;
  difficulty: string;
  time_commitment: string;
  expected_win_rate: string;
  expected_return_monthly: string;
  recommended_capital_min: number;
  leverage: number;
}

export interface RecommendationRequest {
  capital: number;
  experience_level: 'beginner' | 'intermediate' | 'advanced';
  risk_tolerance: 'low' | 'medium' | 'high';
  exchange?: string;
}

export interface BacktestRequest {
  preset_id: string;
  exchange?: string;
  symbol?: string;
  days_back?: number;
  initial_capital: number;
}

export const TradingAPI = {
  // 1. 프리셋 목록 조회
  async getPresets(): Promise<PresetInfo[]> {
    const response = await fetch(`${API_BASE}/presets`);
    if (!response.ok) throw new Error('Failed to fetch presets');
    return response.json();
  },

  // 2. AI 추천
  async getRecommendation(req: RecommendationRequest) {
    const response = await fetch(`${API_BASE}/recommend`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(req)
    });
    if (!response.ok) throw new Error('Failed to get recommendation');
    return response.json();
  },

  // 3. 백테스트 실행
  async runBacktest(req: BacktestRequest) {
    const response = await fetch(`${API_BASE}/quick-backtest`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(req)
    });
    if (!response.ok) throw new Error('Backtest failed');
    return response.json();
  },

  // 4. 시스템 상태 확인
  async getHealth() {
    const response = await fetch(`${API_BASE}/health`);
    if (!response.ok) throw new Error('Health check failed');
    return response.json();
  }
};
```

---

### 2. 프리셋 선택 컴포넌트

```typescript
// src/components/PresetSelector.tsx

import React, { useState, useEffect } from 'react';
import { TradingAPI, PresetInfo } from '../api/tradingApi';

export const PresetSelector: React.FC = () => {
  const [presets, setPresets] = useState<PresetInfo[]>([]);
  const [selectedPreset, setSelectedPreset] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    TradingAPI.getPresets()
      .then(setPresets)
      .catch(err => console.error('Failed to load presets:', err))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div>프리셋 로딩 중...</div>;

  return (
    <div className="preset-selector">
      <h2>트레이딩 프리셋 선택</h2>

      <div className="preset-grid">
        {presets.map(preset => (
          <div
            key={preset.id}
            className={`preset-card ${selectedPreset === preset.id ? 'selected' : ''}`}
            onClick={() => setSelectedPreset(preset.id)}
          >
            {/* 난이도 배지 */}
            <span className={`difficulty-badge ${preset.difficulty.toLowerCase()}`}>
              {preset.difficulty}
            </span>

            {/* 프리셋 이름 */}
            <h3>{preset.name_ko}</h3>

            {/* 설명 */}
            <p className="description">{preset.description_ko}</p>

            {/* 주요 정보 */}
            <div className="preset-info">
              <div className="info-row">
                <span>레버리지:</span>
                <strong>{preset.leverage}배</strong>
              </div>
              <div className="info-row">
                <span>예상 월 수익:</span>
                <strong>{preset.expected_return_monthly}</strong>
              </div>
              <div className="info-row">
                <span>예상 승률:</span>
                <strong>{preset.expected_win_rate}</strong>
              </div>
              <div className="info-row">
                <span>최소 자본금:</span>
                <strong>${preset.recommended_capital_min.toLocaleString()}</strong>
              </div>
              <div className="info-row">
                <span>시간 투입:</span>
                <strong>{preset.time_commitment}</strong>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
```

---

### 3. AI 추천 컴포넌트

```typescript
// src/components/AIRecommendation.tsx

import React, { useState } from 'react';
import { TradingAPI } from '../api/tradingApi';

export const AIRecommendation: React.FC = () => {
  const [capital, setCapital] = useState(5000);
  const [experience, setExperience] = useState<'beginner' | 'intermediate' | 'advanced'>('beginner');
  const [risk, setRisk] = useState<'low' | 'medium' | 'high'>('low');
  const [recommendation, setRecommendation] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const handleGetRecommendation = async () => {
    setLoading(true);
    try {
      const result = await TradingAPI.getRecommendation({
        capital,
        experience_level: experience,
        risk_tolerance: risk
      });
      setRecommendation(result);
    } catch (err) {
      console.error('Recommendation failed:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="ai-recommendation">
      <h2>AI 스마트 추천</h2>

      {/* 입력 폼 */}
      <div className="input-form">
        <div className="form-group">
          <label>자본금 (USD)</label>
          <input
            type="number"
            value={capital}
            onChange={e => setCapital(Number(e.target.value))}
            min={500}
            step={100}
          />
        </div>

        <div className="form-group">
          <label>트레이딩 경험</label>
          <select value={experience} onChange={e => setExperience(e.target.value as any)}>
            <option value="beginner">초보자</option>
            <option value="intermediate">중급자</option>
            <option value="advanced">고급자</option>
          </select>
        </div>

        <div className="form-group">
          <label>리스크 성향</label>
          <select value={risk} onChange={e => setRisk(e.target.value as any)}>
            <option value="low">낮음 (안전)</option>
            <option value="medium">중간 (균형)</option>
            <option value="high">높음 (공격적)</option>
          </select>
        </div>

        <button onClick={handleGetRecommendation} disabled={loading}>
          {loading ? '분석 중...' : 'AI 추천 받기'}
        </button>
      </div>

      {/* 추천 결과 */}
      {recommendation && (
        <div className="recommendation-result">
          <h3>추천 프리셋: {recommendation.recommended_preset.name_ko}</h3>

          <div className="reasoning">
            <h4>추천 이유</h4>
            <p>{recommendation.reasoning_ko}</p>
          </div>

          {/* 경고사항 */}
          {recommendation.warnings.length > 0 && (
            <div className="warnings">
              <h4>주의사항</h4>
              <ul>
                {recommendation.warnings.map((warning: string, i: number) => (
                  <li key={i}>{warning}</li>
                ))}
              </ul>
            </div>
          )}

          {/* 팁 */}
          {recommendation.tips.length > 0 && (
            <div className="tips">
              <h4>유용한 팁</h4>
              <ul>
                {recommendation.tips.map((tip: string, i: number) => (
                  <li key={i}>{tip}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
```

---

### 4. 백테스트 실행 컴포넌트

```typescript
// src/components/BacktestRunner.tsx

import React, { useState } from 'react';
import { TradingAPI } from '../api/tradingApi';

interface Props {
  presetId: string;
  initialCapital: number;
}

export const BacktestRunner: React.FC<Props> = ({ presetId, initialCapital }) => {
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const runBacktest = async () => {
    setLoading(true);
    setError(null);

    try {
      const result = await TradingAPI.runBacktest({
        preset_id: presetId,
        exchange: 'binance',
        days_back: 30,
        initial_capital: initialCapital
      });
      setResult(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : '백테스트 실패');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="backtest-runner">
      <button
        onClick={runBacktest}
        disabled={loading || !presetId}
        className="btn-primary"
      >
        {loading ? '백테스트 실행 중...' : '백테스트 시작'}
      </button>

      {error && (
        <div className="error-message">
          ❌ {error}
        </div>
      )}

      {result && (
        <div className="backtest-results">
          {/* 프리셋 정보 */}
          <div className="preset-summary">
            <h3>{result.preset_info.name_ko}</h3>
            <p>난이도: {result.preset_info.difficulty}</p>
            <p>예상 승률: {result.preset_info.expected_win_rate}</p>
          </div>

          {/* 백테스트 결과 */}
          <div className="results-grid">
            <div className="result-card">
              <h4>총 수익률</h4>
              <p className={result.backtest_result.total_return > 0 ? 'positive' : 'negative'}>
                {result.backtest_result.total_return.toFixed(2)}%
              </p>
            </div>

            <div className="result-card">
              <h4>승률</h4>
              <p>{result.backtest_result.win_rate.toFixed(2)}%</p>
            </div>

            <div className="result-card">
              <h4>총 거래 수</h4>
              <p>{result.backtest_result.total_trades}</p>
            </div>

            <div className="result-card">
              <h4>샤프 비율</h4>
              <p>{result.backtest_result.sharpe_ratio.toFixed(2)}</p>
            </div>

            <div className="result-card">
              <h4>최대 낙폭</h4>
              <p className="negative">
                {result.backtest_result.max_drawdown.toFixed(2)}%
              </p>
            </div>
          </div>

          {/* 예상 vs 실제 */}
          <div className="performance-comparison">
            <h4>성과 비교</h4>
            <p>{result.performance_vs_expected.return_status}</p>
            <p>{result.performance_vs_expected.win_rate_status}</p>
          </div>
        </div>
      )}
    </div>
  );
};
```

---

### 5. 시스템 상태 표시 컴포넌트

```typescript
// src/components/SystemHealth.tsx

import React, { useState, useEffect } from 'react';
import { TradingAPI } from '../api/tradingApi';

export const SystemHealth: React.FC = () => {
  const [health, setHealth] = useState<any>(null);

  useEffect(() => {
    const fetchHealth = async () => {
      try {
        const result = await TradingAPI.getHealth();
        setHealth(result);
      } catch (err) {
        console.error('Health check failed:', err);
      }
    };

    // 초기 로드
    fetchHealth();

    // 5초마다 업데이트
    const interval = setInterval(fetchHealth, 5000);
    return () => clearInterval(interval);
  }, []);

  if (!health) return null;

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy': return 'green';
      case 'degraded': return 'yellow';
      case 'unhealthy': return 'red';
      default: return 'gray';
    }
  };

  return (
    <div className="system-health">
      {/* 전체 상태 */}
      <div className={`status-badge ${getStatusColor(health.status)}`}>
        {health.status === 'healthy' ? '✅' : health.status === 'degraded' ? '⚠️' : '❌'}
        {' '}
        {health.message}
      </div>

      {/* 서킷 브레이커 상태 */}
      <div className="circuit-breakers">
        {health.circuit_breakers.map((cb: any) => (
          <div key={cb.name} className="circuit-breaker">
            <span>{cb.name}</span>
            <span className={`state ${cb.state}`}>{cb.state}</span>
            <div className="health-bar">
              <div
                className="health-fill"
                style={{ width: `${cb.health_percentage}%` }}
              />
            </div>
          </div>
        ))}
      </div>

      {/* 시스템 리소스 */}
      <div className="system-metrics">
        <div className="metric">
          <span>CPU</span>
          <span>{health.system_metrics.cpu_percent}%</span>
        </div>
        <div className="metric">
          <span>메모리</span>
          <span>{health.system_metrics.memory_percent}%</span>
        </div>
        <div className="metric">
          <span>디스크</span>
          <span>{health.system_metrics.disk_percent}%</span>
        </div>
      </div>

      {/* 경고사항 */}
      {health.warnings.length > 0 && (
        <div className="warnings">
          {health.warnings.map((warning: string, i: number) => (
            <div key={i} className="warning">{warning}</div>
          ))}
        </div>
      )}
    </div>
  );
};
```

---

### 6. 전체 앱 통합

```typescript
// src/App.tsx

import React, { useState } from 'react';
import { SystemHealth } from './components/SystemHealth';
import { AIRecommendation } from './components/AIRecommendation';
import { PresetSelector } from './components/PresetSelector';
import { BacktestRunner } from './components/BacktestRunner';

function App() {
  const [selectedPreset, setSelectedPreset] = useState<string>('');
  const [capital, setCapital] = useState(5000);
  const [step, setStep] = useState(1);

  return (
    <div className="app">
      {/* 헤더 및 시스템 상태 */}
      <header>
        <h1>TradingBot AI</h1>
        <SystemHealth />
      </header>

      {/* 단계별 UI */}
      <main>
        {step === 1 && (
          <div className="step">
            <h2>1단계: 자본금 입력</h2>
            <input
              type="number"
              value={capital}
              onChange={e => setCapital(Number(e.target.value))}
              min={500}
            />
            <button onClick={() => setStep(2)}>다음</button>
          </div>
        )}

        {step === 2 && (
          <div className="step">
            <h2>2단계: AI 추천 (선택사항)</h2>
            <AIRecommendation />
            <button onClick={() => setStep(3)}>건너뛰기</button>
          </div>
        )}

        {step === 3 && (
          <div className="step">
            <h2>3단계: 프리셋 선택</h2>
            <PresetSelector
              selectedPreset={selectedPreset}
              onSelect={setSelectedPreset}
            />
            <button
              onClick={() => setStep(4)}
              disabled={!selectedPreset}
            >
              백테스트 실행
            </button>
          </div>
        )}

        {step === 4 && (
          <div className="step">
            <h2>4단계: 백테스트 결과</h2>
            <BacktestRunner
              presetId={selectedPreset}
              initialCapital={capital}
            />
            <button onClick={() => setStep(1)}>처음부터 다시</button>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
```

---

## 🎨 CSS 스타일 예제

```css
/* src/styles/App.css */

.preset-card {
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  padding: 16px;
  cursor: pointer;
  transition: all 0.3s;
}

.preset-card.selected {
  border-color: #4CAF50;
  background-color: #f1f8f4;
}

.preset-card:hover {
  box-shadow: 0 4px 8px rgba(0,0,0,0.1);
  transform: translateY(-2px);
}

.difficulty-badge {
  display: inline-block;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: bold;
}

.difficulty-badge.easy {
  background-color: #4CAF50;
  color: white;
}

.difficulty-badge.medium {
  background-color: #FF9800;
  color: white;
}

.difficulty-badge.hard {
  background-color: #F44336;
  color: white;
}

.result-card .positive {
  color: #4CAF50;
  font-size: 24px;
  font-weight: bold;
}

.result-card .negative {
  color: #F44336;
  font-size: 24px;
  font-weight: bold;
}

.circuit-breaker .state.closed {
  color: #4CAF50;
}

.circuit-breaker .state.open {
  color: #F44336;
}

.circuit-breaker .state.half_open {
  color: #FF9800;
}

.health-bar {
  width: 100%;
  height: 8px;
  background-color: #e0e0e0;
  border-radius: 4px;
  overflow: hidden;
}

.health-fill {
  height: 100%;
  background: linear-gradient(90deg, #F44336, #FF9800, #4CAF50);
  transition: width 0.3s;
}
```

---

## 📱 모바일 반응형

```css
/* 모바일 최적화 */
@media (max-width: 768px) {
  .preset-grid {
    grid-template-columns: 1fr;
  }

  .results-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .system-metrics {
    flex-direction: column;
  }
}
```

---

## 🔧 환경 설정

```typescript
// .env.development
REACT_APP_API_BASE_URL=http://localhost:8001/api/v1

// .env.production
REACT_APP_API_BASE_URL=https://api.yourdomain.com/api/v1
```

```typescript
// src/config.ts
export const config = {
  API_BASE_URL: process.env.REACT_APP_API_BASE_URL || 'http://localhost:8001/api/v1'
};
```

---

## ✅ 통합 체크리스트

### 개발 단계
- [ ] API 클라이언트 설정 완료
- [ ] 프리셋 선택 UI 구현
- [ ] AI 추천 UI 구현 (선택사항)
- [ ] 백테스트 실행 UI 구현
- [ ] 결과 표시 UI 구현
- [ ] 시스템 상태 모니터링 구현
- [ ] 에러 처리 구현
- [ ] 로딩 상태 표시 구현

### 테스트 단계
- [ ] 프리셋 목록 로딩 테스트
- [ ] AI 추천 기능 테스트
- [ ] 백테스트 실행 테스트
- [ ] 시스템 상태 확인 테스트
- [ ] 에러 시나리오 테스트
- [ ] 모바일 반응형 테스트

### 배포 단계
- [ ] 환경 변수 설정
- [ ] API 엔드포인트 설정
- [ ] CORS 설정 확인
- [ ] 프로덕션 빌드 테스트

---

## 🚨 주요 주의사항

### 1. API 키 보안
```typescript
// ❌ 절대 하지 마세요
const API_KEY = 'your_api_key_here';  // 클라이언트에 노출됨!

// ✅ 올바른 방법
// 백엔드에서만 API 키 사용, 프론트엔드는 세션/토큰 사용
```

### 2. 에러 처리
```typescript
try {
  const result = await TradingAPI.runBacktest(req);
  setResult(result);
} catch (err) {
  // 사용자에게 친절한 에러 메시지
  if (err.message.includes('Circuit breaker')) {
    setError('시스템이 일시적으로 사용할 수 없습니다. 잠시 후 다시 시도해주세요.');
  } else {
    setError('백테스트 실행 중 오류가 발생했습니다.');
  }
}
```

### 3. 로딩 상태
```typescript
// 사용자에게 진행 상황 표시
setLoading(true);
try {
  const result = await longRunningOperation();
  // ...
} finally {
  setLoading(false);  // 항상 실행됨
}
```

---

## 📞 지원

문제가 발생하면:
1. 백엔드 로그 확인: `trading-backend/logs/`
2. 시스템 상태 확인: `GET /api/v1/health`
3. 브라우저 콘솔 확인

---

## 🎉 완료!

이제 프론트엔드에서 **3단계**로 백테스트를 실행할 수 있습니다:

1. 자본금 입력 → AI 추천 (선택)
2. 프리셋 선택
3. 백테스트 실행 → 결과 확인

**Happy Coding! 🚀**
