"""
Pine Script Strategy Exporter

Python 전략을 TradingView Pine Script v5로 변환
- 자동 백테스팅 가능
- 롱/숏 시그널 표시
- 익절/손절 레벨 자동 계산 및 표시
"""

from typing import Dict, Optional, List
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class PineScriptStrategy:
    """Pine Script strategy configuration"""
    name: str
    description: str
    strategy_type: str
    parameters: Dict
    leverage: int
    position_size_pct: float
    atr_sl_multiplier: float
    atr_tp_multiplier: float
    commission: float = 0.0004  # Binance default 0.04%


class PineScriptExporter:
    """
    Python 전략을 Pine Script v5로 변환

    Features:
    - 자동 롱/숏 시그널 생성
    - ATR 기반 익절/손절 레벨 자동 계산
    - TradingView 차트에 직접 표시
    - 백테스팅 내장
    - TradingView Webhook 자동 주문 지원
    """

    def __init__(self, webhook_url: Optional[str] = None):
        self.template_version = "v5"
        self.webhook_url = webhook_url or "http://localhost:8001/api/v1/webhook/tradingview"

    def export_strategy(
        self,
        strategy: PineScriptStrategy
    ) -> str:
        """
        전략을 Pine Script v5로 변환

        Args:
            strategy: 전략 설정

        Returns:
            완전한 Pine Script 코드
        """

        # 전략 타입에 따라 적절한 템플릿 선택
        if strategy.strategy_type == "supertrend":
            return self._generate_supertrend_pine(strategy)
        elif strategy.strategy_type == "rsi_ema":
            return self._generate_rsi_ema_pine(strategy)
        elif strategy.strategy_type == "macd_stoch":
            return self._generate_macd_stoch_pine(strategy)
        elif strategy.strategy_type == "ichimoku":
            return self._generate_ichimoku_pine(strategy)
        else:
            # 기본 템플릿
            return self._generate_generic_pine(strategy)

    def _generate_supertrend_pine(self, strategy: PineScriptStrategy) -> str:
        """SuperTrend 전략 Pine Script 생성"""

        period = strategy.parameters.get("period", 10)
        multiplier = strategy.parameters.get("multiplier", 3.0)

        pine_code = f'''// This Pine Script was auto-generated from TradingBot AI
//@version=5
strategy("{strategy.name}",
     overlay=true,
     initial_capital=10000,
     default_qty_type=strategy.percent_of_equity,
     default_qty_value={strategy.position_size_pct * 100},
     commission_type=strategy.commission.percent,
     commission_value={strategy.commission * 100},
     pyramiding=0)

// ==================== 입력 파라미터 ====================
period = input.int({period}, "SuperTrend Period", minval=1)
multiplier = input.float({multiplier}, "SuperTrend Multiplier", minval=0.1, step=0.1)
atr_sl_mult = input.float({strategy.atr_sl_multiplier}, "ATR Stop Loss Multiplier", minval=0.5, step=0.1)
atr_tp_mult = input.float({strategy.atr_tp_multiplier}, "ATR Take Profit Multiplier", minval=0.5, step=0.1)

// ==================== SuperTrend 계산 ====================
[supertrend, direction] = ta.supertrend(multiplier, period)

// 트렌드 방향 (1 = 상승, -1 = 하락)
trendUp = direction < 0
trendDown = direction > 0

// 색상
uptrendColor = color.new(color.green, 0)
downtrendColor = color.new(color.red, 0)

// SuperTrend 라인 표시
plot(supertrend, color=trendUp ? uptrendColor : downtrendColor, linewidth=2, title="SuperTrend")

// ==================== ATR 기반 익절/손절 ====================
atr = ta.atr(14)

// 현재 포지션 진입가
var float entryPrice = na
var float stopLoss = na
var float takeProfit = na

// ==================== 롱/숏 시그널 ====================
// 롱 시그널: SuperTrend가 하락 → 상승으로 전환
longSignal = ta.crossover(close, supertrend) and trendUp

// 숏 시그널: SuperTrend가 상승 → 하락으로 전환
shortSignal = ta.crossunder(close, supertrend) and trendDown

// ==================== 진입 로직 ====================
if (longSignal and strategy.position_size == 0)
    entryPrice := close
    stopLoss := close - (atr * atr_sl_mult)
    takeProfit := close + (atr * atr_tp_mult)

    strategy.entry("롱 진입", strategy.long)
    strategy.exit("롱 청산", "롱 진입",
         stop=stopLoss,
         limit=takeProfit)

    // 진입 시그널 표시
    label.new(bar_index, low, "LONG\\n진입",
         style=label.style_label_up,
         color=color.new(color.green, 0),
         textcolor=color.white,
         size=size.normal)

if (shortSignal and strategy.position_size == 0)
    entryPrice := close
    stopLoss := close + (atr * atr_sl_mult)
    takeProfit := close - (atr * atr_tp_mult)

    strategy.entry("숏 진입", strategy.short)
    strategy.exit("숏 청산", "숏 진입",
         stop=stopLoss,
         limit=takeProfit)

    // 진입 시그널 표시
    label.new(bar_index, high, "SHORT\\n진입",
         style=label.style_label_down,
         color=color.new(color.red, 0),
         textcolor=color.white,
         size=size.normal)

// ==================== 익절/손절 라인 표시 ====================
// 현재 포지션이 있을 때만 표시
isLong = strategy.position_size > 0
isShort = strategy.position_size < 0

// 익절/손절 라인 그리기
var line slLine = na
var line tpLine = na
var label slLabel = na
var label tpLabel = na

if (isLong or isShort)
    // 이전 라인 삭제
    if not na(slLine)
        line.delete(slLine)
        line.delete(tpLine)
        label.delete(slLabel)
        label.delete(tpLabel)

    // 새 라인 생성
    slLine := line.new(bar_index - 1, stopLoss, bar_index, stopLoss,
         color=color.new(color.red, 0),
         width=2,
         style=line.style_dashed)

    tpLine := line.new(bar_index - 1, takeProfit, bar_index, takeProfit,
         color=color.new(color.green, 0),
         width=2,
         style=line.style_dashed)

    // 라벨 추가
    slLabel := label.new(bar_index, stopLoss, "손절: " + str.tostring(stopLoss, "#.##"),
         style=label.style_label_left,
         color=color.new(color.red, 70),
         textcolor=color.red,
         size=size.small)

    tpLabel := label.new(bar_index, takeProfit, "익절: " + str.tostring(takeProfit, "#.##"),
         style=label.style_label_left,
         color=color.new(color.green, 70),
         textcolor=color.green,
         size=size.small)

// ==================== 차트 배경 색상 ====================
// 롱 포지션: 녹색 배경
// 숏 포지션: 빨간색 배경
bgColor = isLong ? color.new(color.green, 95) : isShort ? color.new(color.red, 95) : na
bgcolor(bgColor)

// ==================== 통계 정보 표시 ====================
// 우측 상단에 현재 상태 표시
var table statsTable = table.new(position.top_right, 2, 6,
     border_width=1,
     border_color=color.gray,
     frame_width=1,
     frame_color=color.gray)

if barstate.islast
    // 헤더
    table.cell(statsTable, 0, 0, "항목", bgcolor=color.new(color.blue, 80), text_color=color.white)
    table.cell(statsTable, 1, 0, "값", bgcolor=color.new(color.blue, 80), text_color=color.white)

    // 현재 포지션
    posText = isLong ? "롱" : isShort ? "숏" : "없음"
    posColor = isLong ? color.green : isShort ? color.red : color.gray
    table.cell(statsTable, 0, 1, "포지션", text_color=color.white)
    table.cell(statsTable, 1, 1, posText, text_color=posColor)

    // 진입가
    if (isLong or isShort)
        table.cell(statsTable, 0, 2, "진입가", text_color=color.white)
        table.cell(statsTable, 1, 2, str.tostring(entryPrice, "#.##"), text_color=color.white)

        // 손절가
        table.cell(statsTable, 0, 3, "손절", text_color=color.white)
        table.cell(statsTable, 1, 3, str.tostring(stopLoss, "#.##"), text_color=color.red)

        // 익절가
        table.cell(statsTable, 0, 4, "익절", text_color=color.white)
        table.cell(statsTable, 1, 4, str.tostring(takeProfit, "#.##"), text_color=color.green)

        // 현재 손익
        pnl = isLong ? (close - entryPrice) / entryPrice * 100 : (entryPrice - close) / entryPrice * 100
        pnlColor = pnl > 0 ? color.green : color.red
        table.cell(statsTable, 0, 5, "현재 손익", text_color=color.white)
        table.cell(statsTable, 1, 5, str.tostring(pnl, "#.##") + "%", text_color=pnlColor)

// ==================== 경고 알림 설정 ====================
// TradingView 알림 기능과 연동
alertcondition(longSignal, title="롱 시그널", message="{{ticker}} 롱 진입 시그널 발생!")
alertcondition(shortSignal, title="숏 시그널", message="{{ticker}} 숏 진입 시그널 발생!")

// 익절/손절 알림
alertcondition(ta.cross(close, takeProfit), title="익절 도달", message="{{ticker}} 익절가 도달!")
alertcondition(ta.cross(close, stopLoss), title="손절 도달", message="{{ticker}} 손절가 도달!")
'''

        return pine_code

    def _generate_rsi_ema_pine(self, strategy: PineScriptStrategy) -> str:
        """RSI + EMA 크로스오버 전략 Pine Script 생성"""

        rsi_period = strategy.parameters.get("rsi_period", 14)
        rsi_overbought = strategy.parameters.get("rsi_overbought", 70)
        rsi_oversold = strategy.parameters.get("rsi_oversold", 30)
        ema_fast = strategy.parameters.get("ema_fast", 9)
        ema_slow = strategy.parameters.get("ema_slow", 21)

        pine_code = f'''// This Pine Script was auto-generated from TradingBot AI
//@version=5
strategy("{strategy.name}",
     overlay=true,
     initial_capital=10000,
     default_qty_type=strategy.percent_of_equity,
     default_qty_value={strategy.position_size_pct * 100},
     commission_type=strategy.commission.percent,
     commission_value={strategy.commission * 100})

// ==================== 입력 파라미터 ====================
rsi_period = input.int({rsi_period}, "RSI Period", minval=2)
rsi_overbought = input.int({rsi_overbought}, "RSI Overbought", minval=50, maxval=100)
rsi_oversold = input.int({rsi_oversold}, "RSI Oversold", minval=0, maxval=50)
ema_fast = input.int({ema_fast}, "EMA Fast", minval=1)
ema_slow = input.int({ema_slow}, "EMA Slow", minval=1)
atr_sl_mult = input.float({strategy.atr_sl_multiplier}, "ATR Stop Loss Multiplier", minval=0.5, step=0.1)
atr_tp_mult = input.float({strategy.atr_tp_multiplier}, "ATR Take Profit Multiplier", minval=0.5, step=0.1)

// ==================== 지표 계산 ====================
rsi = ta.rsi(close, rsi_period)
ema_fast_line = ta.ema(close, ema_fast)
ema_slow_line = ta.ema(close, ema_slow)
atr = ta.atr(14)

// EMA 크로스오버
ema_bullish = ta.crossover(ema_fast_line, ema_slow_line)
ema_bearish = ta.crossunder(ema_fast_line, ema_slow_line)

// ==================== 진입 시그널 ====================
// 롱: EMA 골든크로스 + RSI 과매도 회복
longSignal = ema_bullish and rsi > rsi_oversold and rsi < 50

// 숏: EMA 데드크로스 + RSI 과매수 회복
shortSignal = ema_bearish and rsi < rsi_overbought and rsi > 50

// ==================== 차트에 EMA 표시 ====================
plot(ema_fast_line, color=color.new(color.blue, 0), linewidth=2, title="EMA Fast")
plot(ema_slow_line, color=color.new(color.orange, 0), linewidth=2, title="EMA Slow")

// ==================== 익절/손절 ====================
var float entryPrice = na
var float stopLoss = na
var float takeProfit = na

if (longSignal and strategy.position_size == 0)
    entryPrice := close
    stopLoss := close - (atr * atr_sl_mult)
    takeProfit := close + (atr * atr_tp_mult)

    strategy.entry("롱 진입", strategy.long)
    strategy.exit("롱 청산", "롱 진입", stop=stopLoss, limit=takeProfit)

    label.new(bar_index, low, "LONG\\nRSI:" + str.tostring(rsi, "#.#"),
         style=label.style_label_up,
         color=color.new(color.green, 0),
         textcolor=color.white)

if (shortSignal and strategy.position_size == 0)
    entryPrice := close
    stopLoss := close + (atr * atr_sl_mult)
    takeProfit := close - (atr * atr_tp_mult)

    strategy.entry("숏 진입", strategy.short)
    strategy.exit("숏 청산", "숏 진입", stop=stopLoss, limit=takeProfit)

    label.new(bar_index, high, "SHORT\\nRSI:" + str.tostring(rsi, "#.#"),
         style=label.style_label_down,
         color=color.new(color.red, 0),
         textcolor=color.white)

// ==================== RSI 차트 (하단) ====================
hline(rsi_overbought, "Overbought", color=color.red, linestyle=hline.style_dashed)
hline(rsi_oversold, "Oversold", color=color.green, linestyle=hline.style_dashed)
hline(50, "Midline", color=color.gray, linestyle=hline.style_dotted)

// 배경색: 과매수/과매도 영역
rsi_bg = rsi > rsi_overbought ? color.new(color.red, 90) :
         rsi < rsi_oversold ? color.new(color.green, 90) : na

// ==================== 알림 ====================
alertcondition(longSignal, title="RSI+EMA 롱 시그널", message="{{ticker}} 롱 진입!")
alertcondition(shortSignal, title="RSI+EMA 숏 시그널", message="{{ticker}} 숏 진입!")
'''

        return pine_code

    def _generate_generic_pine(self, strategy: PineScriptStrategy) -> str:
        """기본 템플릿 Pine Script"""

        pine_code = f'''// This Pine Script was auto-generated from TradingBot AI
//@version=5
strategy("{strategy.name}",
     overlay=true,
     initial_capital=10000,
     default_qty_type=strategy.percent_of_equity,
     default_qty_value={strategy.position_size_pct * 100},
     commission_type=strategy.commission.percent,
     commission_value={strategy.commission * 100})

// ==================== 기본 설정 ====================
atr_sl_mult = input.float({strategy.atr_sl_multiplier}, "ATR Stop Loss Multiplier")
atr_tp_mult = input.float({strategy.atr_tp_multiplier}, "ATR Take Profit Multiplier")

// ATR 계산
atr = ta.atr(14)

// ==================== 전략 로직 ====================
// 여기에 커스텀 전략 로직을 추가하세요

// 예시: 간단한 이동평균 크로스오버
ma_fast = ta.sma(close, 20)
ma_slow = ta.sma(close, 50)

longSignal = ta.crossover(ma_fast, ma_slow)
shortSignal = ta.crossunder(ma_fast, ma_slow)

// ==================== 진입/청산 ====================
var float stopLoss = na
var float takeProfit = na

if (longSignal)
    stopLoss := close - (atr * atr_sl_mult)
    takeProfit := close + (atr * atr_tp_mult)
    strategy.entry("롱", strategy.long)
    strategy.exit("롱 청산", "롱", stop=stopLoss, limit=takeProfit)

if (shortSignal)
    stopLoss := close + (atr * atr_sl_mult)
    takeProfit := close - (atr * atr_tp_mult)
    strategy.entry("숏", strategy.short)
    strategy.exit("숏 청산", "숏", stop=stopLoss, limit=takeProfit)

// 차트 표시
plot(ma_fast, "Fast MA", color=color.blue)
plot(ma_slow, "Slow MA", color=color.red)
'''

        return pine_code

    def generate_from_preset(
        self,
        preset_id: str,
        from_presets_module: bool = True
    ) -> str:
        """
        프리셋에서 Pine Script 생성

        Args:
            preset_id: 프리셋 ID (예: "balanced_trader")
            from_presets_module: True면 app.core.presets에서 가져옴

        Returns:
            Pine Script 코드
        """

        if from_presets_module:
            from app.core.presets import get_preset
            preset = get_preset(preset_id)

            if not preset:
                raise ValueError(f"Unknown preset: {preset_id}")

            strategy = PineScriptStrategy(
                name=preset.name,
                description=preset.description,
                strategy_type=preset.strategy_type,
                parameters=preset.strategy_params,
                leverage=preset.leverage,
                position_size_pct=preset.position_size_pct,
                atr_sl_multiplier=preset.atr_sl_multiplier,
                atr_tp_multiplier=preset.atr_tp_multiplier
            )

            return self.export_strategy(strategy)

        raise NotImplementedError("Direct preset dict not yet supported")


    def add_webhook_alerts(
        self,
        account_id: str,
        exchange: str,
        symbol: str,
        leverage: int,
        secret: str
    ) -> str:
        """
        웹훅 알림 코드 생성

        TradingView 알림에서 사용할 JSON 페이로드 생성

        Args:
            account_id: 사용자 계정 ID
            exchange: 거래소 (binance or okx)
            symbol: 심볼 (BTCUSDT)
            leverage: 레버리지
            secret: 웹훅 검증 키

        Returns:
            Pine Script 웹훅 알림 코드
        """

        # 웹훅 알림 코드 (Pine Script에 추가)
        webhook_code = f'''
// ==================== TradingView Webhook 자동 주문 ====================
// 아래 코드를 TradingView 알림 설정의 "Message" 필드에 복사하세요

// 롱 진입 알림
if (longSignal and strategy.position_size == 0)
    alert('{{"account_id":"{account_id}","exchange":"{exchange}","action":"long","symbol":"{symbol}","leverage":{leverage},"secret":"{secret}"}}', alert.freq_once_per_bar_close)

// 숏 진입 알림
if (shortSignal and strategy.position_size == 0)
    alert('{{"account_id":"{account_id}","exchange":"{exchange}","action":"short","symbol":"{symbol}","leverage":{leverage},"secret":"{secret}"}}', alert.freq_once_per_bar_close)

// 익절 알림 (롱)
if (strategy.position_size > 0 and ta.cross(close, takeProfit))
    alert('{{"account_id":"{account_id}","exchange":"{exchange}","action":"close_long","symbol":"{symbol}","secret":"{secret}"}}', alert.freq_once_per_bar_close)

// 익절 알림 (숏)
if (strategy.position_size < 0 and ta.cross(close, takeProfit))
    alert('{{"account_id":"{account_id}","exchange":"{exchange}","action":"close_short","symbol":"{symbol}","secret":"{secret}"}}', alert.freq_once_per_bar_close)

// 손절 알림 (롱)
if (strategy.position_size > 0 and ta.cross(close, stopLoss))
    alert('{{"account_id":"{account_id}","exchange":"{exchange}","action":"close_long","symbol":"{symbol}","secret":"{secret}"}}', alert.freq_once_per_bar_close)

// 손절 알림 (숏)
if (strategy.position_size < 0 and ta.cross(close, stopLoss))
    alert('{{"account_id":"{account_id}","exchange":"{exchange}","action":"close_short","symbol":"{symbol}","secret":"{secret}"}}', alert.freq_once_per_bar_close)

// ==================== TradingView 알림 설정 방법 ====================
// 1. TradingView 차트에서 "알림 생성" 클릭
// 2. 조건: "{account_id}의 전략" 선택
// 3. 메시지에 위 JSON 코드 붙여넣기
// 4. Webhook URL: {self.webhook_url}
// 5. "알림 생성" 클릭

'''

        return webhook_code

    def generate_webhook_setup_guide(
        self,
        account_id: str,
        exchange: str,
        secret: str
    ) -> str:
        """
        웹훅 설정 가이드 생성

        Args:
            account_id: 사용자 계정 ID
            exchange: 거래소
            secret: 웹훅 검증 키

        Returns:
            설정 가이드 마크다운
        """

        guide = f"""
# TradingView Webhook 자동 주문 설정 가이드

## 1. API 키 등록

먼저 거래소 API 키를 등록해야 합니다.

**Binance 사용자:**
```bash
POST {self.webhook_url.replace('/webhook/tradingview', '/accounts/binance/register')}

{{
  "account_id": "{account_id}",
  "api_key": "YOUR_BINANCE_API_KEY",
  "api_secret": "YOUR_BINANCE_API_SECRET",
  "testnet": true
}}
```

**OKX 사용자:**
```bash
POST {self.webhook_url.replace('/webhook/tradingview', '/accounts/okx/register')}

{{
  "account_id": "{account_id}",
  "api_key": "YOUR_OKX_API_KEY",
  "api_secret": "YOUR_OKX_API_SECRET",
  "passphrase": "YOUR_OKX_PASSPHRASE",
  "testnet": true
}}
```

## 2. Pine Script에 웹훅 코드 추가

Pine Script의 전략 코드 맨 아래에 웹훅 알림 코드를 추가하세요.

## 3. TradingView 알림 생성

1. TradingView 차트에서 "알림 생성" (시계 아이콘) 클릭
2. **조건**: 사용 중인 전략 선택
3. **알림 작업**: "Webhook URL" 체크
4. **Webhook URL**: `{self.webhook_url}`
5. **메시지**:
   ```json
   {{"account_id":"{account_id}","exchange":"{exchange}","action":"long","symbol":"BTCUSDT","leverage":10,"secret":"{secret}"}}
   ```

6. **빈도**: "Once Per Bar Close" 권장
7. "알림 생성" 클릭

## 4. 보안 주의사항

⚠️ **중요:**
- `secret` 키는 절대 공유하지 마세요
- API 키는 반드시 IP 제한을 설정하세요
- 처음에는 testnet으로 테스트하세요
- 실계좌 사용 전 충분히 검증하세요

## 5. 웹훅 페이로드 형식

```json
{{
  "account_id": "사용자계정ID",
  "exchange": "binance",  // 또는 "okx"
  "action": "long",       // long, short, close_long, close_short, close_all
  "symbol": "BTCUSDT",
  "price": 50000,         // 선택사항
  "quantity": 0.01,       // 선택사항 (미지정시 계좌의 10% 사용)
  "leverage": 10,         // 선택사항
  "stop_loss": 48000,     // 선택사항
  "take_profit": 52000,   // 선택사항
  "secret": "{secret}"
}}
```

## 6. 테스트

웹훅이 제대로 작동하는지 확인:
```bash
GET {self.webhook_url.replace('/webhook/tradingview', '/webhook/health')}
```

계정 상태 확인:
```bash
GET {self.webhook_url.replace('/webhook/tradingview', '/accounts/status/')}{account_id}?exchange={exchange}
```

## 문제 해결

**주문이 실행되지 않는 경우:**
1. API 키가 올바르게 등록되었는지 확인
2. 웹훅 secret이 일치하는지 확인
3. 거래소 계정에 충분한 잔액이 있는지 확인
4. 백엔드 서버가 실행 중인지 확인

**에러 로그 확인:**
```bash
GET {self.webhook_url.replace('/webhook/tradingview', '/accounts/list')}
```
"""

        return guide


def get_pine_exporter(webhook_url: Optional[str] = None) -> PineScriptExporter:
    """Get Pine Script exporter instance"""
    return PineScriptExporter(webhook_url=webhook_url)
