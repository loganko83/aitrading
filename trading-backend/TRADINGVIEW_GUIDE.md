# TradingView Pine Script 통합 가이드

## ✅ 가능한 것

### 1. Pine Script 자동 변환 ✅
- Python 전략 → Pine Script v5 자동 변환
- 모든 프리셋 지원
- SuperTrend, RSI+EMA, MACD 등 모든 전략

### 2. TradingView 백테스팅 ✅
- TradingView 내장 백테스팅 엔진 사용
- 실시간 데이터로 백테스트
- 성과 통계 자동 표시

### 3. 시그널 자동 표시 ✅
- **롱 진입**: 녹색 화살표 (차트 하단)
- **숏 진입**: 빨간색 화살표 (차트 상단)
- **익절가**: 녹색 점선 (ATR 기반 자동 계산)
- **손절가**: 빨간색 점선 (ATR 기반 자동 계산)
- **현재 손익**: 우측 상단 테이블

### 4. 알림 시스템 ✅
- 롱/숏 진입 시그널 알림
- 익절/손절 도달 알림
- 이메일, SMS, 앱 푸시 알림 지원

---

## ❌ 불가능한 것

### 자동 업로드 ❌
- TradingView는 **공식 업로드 API를 제공하지 않음**
- **수동 복사-붙여넣기 필요**
- 보안상의 이유로 자동 업로드 불가

**하지만!** 복사-붙여넣기는 **30초면 완료**됩니다!

---

## 📝 사용 방법 (3단계)

### 1단계: Pine Script 생성

```bash
POST /api/v1/simple/export-pine-script
Content-Type: application/json

{
  "preset_id": "balanced_trader"
}
```

**응답:**

```json
{
  "success": true,
  "preset_name": "균형잡힌 트레이더",
  "pine_script_code": "// @version=5\nstrategy(\"Balanced Trader\"...",
  "instructions_ko": "TradingView에서 이 Pine Script 사용하는 방법...",
  "features": [
    "✅ TradingView Pine Script v5",
    "✅ 자동 백테스팅",
    "✅ 롱/숏 시그널 자동 표시"
  ]
}
```

### 2단계: TradingView에 붙여넣기

1. **TradingView 접속**
   - https://www.tradingview.com
   - 로그인 (무료 계정 가능)

2. **차트 열기**
   - 원하는 심볼 선택 (예: BTCUSDT)
   - 타임프레임 설정 (예: 1H)

3. **Pine Editor 열기**
   - 화면 하단의 "Pine Editor" 탭 클릭
   - 또는 단축키: `Ctrl+Alt+E` (Windows), `Cmd+Opt+E` (Mac)

4. **코드 붙여넣기**
   - "새 스크립트" 클릭
   - API 응답의 `pine_script_code` 전체 복사
   - Pine Editor에 붙여넣기
   - 스크립트 이름 변경 (예: "내 SuperTrend 전략")

5. **저장 및 적용**
   - "저장" 클릭 (`Ctrl+S`)
   - "차트에 추가" 클릭

### 3단계: 백테스트 결과 확인

**자동으로 표시되는 정보:**

1. **차트 시그널**
   - 롱 진입: 녹색 라벨 "LONG 진입"
   - 숏 진입: 빨간색 라벨 "SHORT 진입"
   - 익절/손절: 점선으로 표시

2. **우측 상단 테이블**
   - 현재 포지션 (롱/숏/없음)
   - 진입가
   - 손절가
   - 익절가
   - 현재 손익 (%)

3. **Strategy Tester 탭** (하단)
   - 총 거래 수
   - 승률 (%)
   - 순이익
   - 최대 낙폭
   - 샤프 비율
   - 모든 거래 내역

---

## 🎨 시그널 표시 예시

### SuperTrend 전략

```
차트 예시:

가격 ↑
   |
   |     🔴 SHORT (빨간색 화살표)
   |    ┌─ 손절: $67,500 (빨간 점선)
   |    │
   |    │  SuperTrend (빨간선)
   |────┼──────────────────────
   |    │  SuperTrend (녹색선)
   |    │
   |    └─ 익절: $64,000 (녹색 점선)
   |     🟢 LONG (녹색 화살표)
   |
가격 ↓
```

### 우측 상단 테이블

```
┌──────────┬──────────┐
│ 항목     │ 값       │
├──────────┼──────────┤
│ 포지션   │ 롱 (녹색)│
│ 진입가   │ 65,000   │
│ 손절     │ 63,500   │
│ 익절     │ 68,000   │
│ 현재손익 │ +2.5%    │
└──────────┴──────────┘
```

---

## 🔔 알림 설정

### 알림 생성 방법

1. **TradingView 차트에서**
   - 우측의 "알림" 아이콘 클릭
   - "생성" 클릭

2. **조건 선택**
   - 조건: "롱 시그널" 또는 "숏 시그널"
   - 옵션: "한 번만" 또는 "매번 알림"

3. **알림 방법**
   - 웹 알림 (기본)
   - 이메일 알림
   - SMS 알림 (Pro+ 계정)
   - 웹훅 URL (자동 거래 연동)

4. **메시지 커스터마이징**
   ```
   {{ticker}} 롱 진입 시그널 발생!
   현재가: {{close}}
   시간: {{time}}
   ```

---

## 📱 프론트엔드 통합 예제

### React 컴포넌트

```typescript
// src/components/PineScriptExporter.tsx

import React, { useState } from 'react';
import { TradingAPI } from '../api/tradingApi';

export const PineScriptExporter: React.FC<{ presetId: string }> = ({ presetId }) => {
  const [pineScript, setPineScript] = useState<string>('');
  const [showInstructions, setShowInstructions] = useState(false);
  const [copied, setCopied] = useState(false);

  const exportToPineScript = async () => {
    try {
      const response = await fetch('http://localhost:8001/api/v1/simple/export-pine-script', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ preset_id: presetId })
      });

      const result = await response.json();
      setPineScript(result.pine_script_code);
      setShowInstructions(true);
    } catch (err) {
      console.error('Pine Script export failed:', err);
    }
  };

  const copyToClipboard = () => {
    navigator.clipboard.writeText(pineScript);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="pine-script-exporter">
      <button onClick={exportToPineScript} className="btn-export">
        📊 TradingView로 내보내기
      </button>

      {showInstructions && (
        <div className="instructions-modal">
          <h3>TradingView Pine Script</h3>

          <div className="code-block">
            <button onClick={copyToClipboard} className="btn-copy">
              {copied ? '✅ 복사됨!' : '📋 코드 복사'}
            </button>
            <pre>{pineScript}</pre>
          </div>

          <div className="steps">
            <h4>사용 방법:</h4>
            <ol>
              <li>TradingView.com 접속</li>
              <li>Pine Editor 열기 (하단)</li>
              <li>"새 스크립트" 클릭</li>
              <li>위 코드 복사하여 붙여넣기</li>
              <li>"차트에 추가" 클릭</li>
              <li>백테스트 결과 자동 표시!</li>
            </ol>
          </div>

          <div className="features">
            <h4>기능:</h4>
            <ul>
              <li>✅ 롱/숏 시그널 자동 표시</li>
              <li>✅ ATR 기반 익절/손절</li>
              <li>✅ 실시간 손익 계산</li>
              <li>✅ 알림 설정 가능</li>
            </ul>
          </div>

          <a
            href="https://www.tradingview.com/chart/"
            target="_blank"
            rel="noopener noreferrer"
            className="btn-open-tradingview"
          >
            🚀 TradingView 열기
          </a>
        </div>
      )}
    </div>
  );
};
```

### CSS 스타일

```css
/* Pine Script Exporter Styles */
.pine-script-exporter {
  padding: 20px;
}

.btn-export {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 12px 24px;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  cursor: pointer;
  transition: transform 0.2s;
}

.btn-export:hover {
  transform: scale(1.05);
}

.instructions-modal {
  margin-top: 20px;
  padding: 20px;
  background: #f5f5f5;
  border-radius: 8px;
}

.code-block {
  position: relative;
  margin: 20px 0;
}

.code-block pre {
  background: #1e1e1e;
  color: #d4d4d4;
  padding: 16px;
  border-radius: 4px;
  overflow-x: auto;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 14px;
  max-height: 400px;
}

.btn-copy {
  position: absolute;
  top: 10px;
  right: 10px;
  background: #4CAF50;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
}

.steps ol, .features ul {
  line-height: 1.8;
}

.btn-open-tradingview {
  display: inline-block;
  margin-top: 16px;
  padding: 12px 24px;
  background: #2962ff;
  color: white;
  text-decoration: none;
  border-radius: 8px;
  font-weight: bold;
}
```

---

## 🎯 지원하는 전략

모든 프리셋에 대해 Pine Script 변환 지원:

| 프리셋 ID | 전략 | Pine Script 기능 |
|-----------|------|------------------|
| beginner_safe | SuperTrend | ✅ 완전 지원 |
| conservative_growth | Multi-Indicator | ✅ 완전 지원 |
| balanced_trader | SuperTrend | ✅ 완전 지원 |
| aggressive_growth | RSI + EMA | ✅ 완전 지원 |
| professional | Multi-Indicator | ✅ 완전 지원 |

---

## 📊 Pine Script 기능 비교

### 우리 시스템 vs TradingView

| 기능 | Python Backend | Pine Script | 비고 |
|------|----------------|-------------|------|
| 백테스팅 | ✅ 자체 엔진 | ✅ TradingView 엔진 | 둘 다 가능 |
| 실시간 트레이딩 | ✅ Binance/OKX API | ❌ 수동 주문 | Python 우세 |
| 차트 시각화 | ❌ 없음 | ✅ 강력한 차트 | TradingView 우세 |
| 시그널 알림 | ✅ API 기반 | ✅ 내장 알림 | 둘 다 가능 |
| 커스터마이징 | ✅ 완전 자유 | ✅ Pine Script 제약 | Python 우세 |
| 접근성 | ❌ 코딩 필요 | ✅ 웹 UI | TradingView 우세 |

**결론**: 백테스트는 TradingView, 실제 트레이딩은 Python!

---

## 🚀 고급 활용

### 1. 웹훅으로 자동 거래 연동

```pine
// Pine Script에서 웹훅 알림 생성
alertcondition(longSignal, title="롱 시그널", message='{"action":"buy","symbol":"{{ticker}}","price":{{close}}}')
```

```python
# Python 백엔드에서 웹훅 수신
@app.post("/webhook/tradingview")
async def handle_tradingview_webhook(data: dict):
    if data["action"] == "buy":
        # 실제 Binance 주문 실행
        await execute_binance_order(
            symbol=data["symbol"],
            side="BUY",
            price=data["price"]
        )
```

### 2. 멀티 타임프레임 분석

```pine
// Pine Script: 멀티 타임프레임 SuperTrend
supertrend_1h = request.security(syminfo.tickerid, "60", ta.supertrend(3.0, 10))
supertrend_4h = request.security(syminfo.tickerid, "240", ta.supertrend(3.0, 10))

// 두 타임프레임 모두 상승 시그널일 때만 진입
longSignal = supertrend_1h > 0 and supertrend_4h > 0
```

### 3. 볼륨 필터 추가

```pine
// Pine Script: 평균 볼륨 필터
avgVolume = ta.sma(volume, 20)
highVolume = volume > avgVolume * 1.5

// 높은 거래량일 때만 진입
longSignal = longSignal and highVolume
```

---

## ❓ FAQ

### Q: 자동 업로드가 정말 불가능한가요?
**A**: 네, TradingView는 보안상의 이유로 공식 API를 제공하지 않습니다. 하지만 복사-붙여넣기는 30초면 완료되므로 큰 불편함은 없습니다.

### Q: Pine Script 무료인가요?
**A**: 네, Pine Script는 TradingView 무료 계정에서도 사용 가능합니다. 다만, 차트 저장 개수 등에 제한이 있습니다.

### Q: 실시간 데이터로 백테스트 되나요?
**A**: 네, TradingView는 실시간 시장 데이터를 사용하여 백테스트를 실행합니다.

### Q: 알림 설정에 비용이 드나요?
**A**: 기본 알림(웹, 이메일)은 무료입니다. SMS 알림은 Pro+ 계정이 필요합니다.

### Q: Python 백테스트 vs TradingView 어느 것이 더 정확한가요?
**A**: 두 시스템 모두 동일한 로직을 사용하므로 결과는 거의 동일합니다. TradingView는 실시간 데이터, Python은 과거 데이터 기반이라는 차이만 있습니다.

---

## 📝 요약

### ✅ 할 수 있는 것
1. 모든 프리셋을 Pine Script로 변환
2. TradingView에서 백테스팅
3. 롱/숏/익절/손절 시그널 자동 표시
4. 알림 설정
5. 웹훅으로 자동 거래 연동

### ❌ 할 수 없는 것
1. TradingView에 자동 업로드 (수동 복사-붙여넣기 필요)

### 🎯 권장 워크플로우
1. **Python Backend**: 전략 개발 및 백테스트
2. **Pine Script Export**: TradingView로 내보내기
3. **TradingView**: 차트 시각화 및 시그널 확인
4. **Webhook**: 실제 거래는 Python Backend로 자동 실행

**최고의 조합!** 🚀
