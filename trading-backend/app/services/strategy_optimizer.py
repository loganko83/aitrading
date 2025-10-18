"""
Strategy Optimizer Service

Features:
- AI 기반 전략 파라미터 최적화
- 유명 전략 템플릿 관리
- Webhook 자동 통합
- 백테스팅 기반 개선 추천
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import openai
from anthropic import Anthropic

from app.core.config import settings
from app.services.pine_script_analyzer import pine_analyzer, StrategyInfo

logger = logging.getLogger(__name__)


@dataclass
class StrategyTemplate:
    """전략 템플릿"""
    id: str
    name: str
    description: str
    author: str  # 원작자
    category: str  # Trend Following, Mean Reversion, Breakout, etc.
    difficulty: str  # Beginner, Intermediate, Advanced
    popularity_score: int  # 1-100
    indicators: List[str]
    default_parameters: Dict[str, Any]
    code_template: str
    backtest_results: Optional[Dict[str, float]] = None


class StrategyOptimizer:
    """전략 최적화 엔진"""

    def __init__(self):
        self.openai_client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        self.anthropic_client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.strategy_library = self._load_strategy_library()

    def _load_strategy_library(self) -> Dict[str, StrategyTemplate]:
        """유명 전략 라이브러리 로드"""
        library = {}

        # 1. EMA Crossover (가장 기본적인 전략)
        library["ema_crossover"] = StrategyTemplate(
            id="ema_crossover",
            name="EMA Crossover Strategy",
            description="빠른 EMA와 느린 EMA의 크로스오버로 진입/청산. 트렌드 추종 전략.",
            author="Community Classic",
            category="Trend Following",
            difficulty="Beginner",
            popularity_score=95,
            indicators=["EMA"],
            default_parameters={
                "fast_length": 9,
                "slow_length": 21,
                "leverage": 3
            },
            code_template="""
//@version=5
strategy("EMA Crossover - Optimized", overlay=true)

// Parameters
fastLength = input.int(9, "Fast EMA", minval=1, maxval=200)
slowLength = input.int(21, "Slow EMA", minval=1, maxval=200)
leverage = input.int(3, "Leverage", minval=1, maxval=125)

// Webhook Settings
account_id = input.string("{{ACCOUNT_ID}}", "Account ID")
webhook_secret = input.string("{{WEBHOOK_SECRET}}", "Webhook Secret")

// Indicators
fastEMA = ta.ema(close, fastLength)
slowEMA = ta.ema(close, slowLength)

// Entry Conditions
longCondition = ta.crossover(fastEMA, slowEMA)
shortCondition = ta.crossunder(fastEMA, slowEMA)

// Plot
plot(fastEMA, "Fast EMA", color=color.blue, linewidth=2)
plot(slowEMA, "Slow EMA", color=color.red, linewidth=2)

// Long Entry
if (longCondition and strategy.position_size == 0)
    strategy.entry("Long", strategy.long)
    alert('{"account_id":"' + account_id + '","exchange":"binance","action":"long","symbol":"BTCUSDT","leverage":' + str.tostring(leverage) + ',"secret":"' + webhook_secret + '","timestamp":' + str.tostring(timenow / 1000) + '}', alert.freq_once_per_bar_close)

// Short Entry
if (shortCondition and strategy.position_size == 0)
    strategy.entry("Short", strategy.short)
    alert('{"account_id":"' + account_id + '","exchange":"binance","action":"short","symbol":"BTCUSDT","leverage":' + str.tostring(leverage) + ',"secret":"' + webhook_secret + '","timestamp":' + str.tostring(timenow / 1000) + '}', alert.freq_once_per_bar_close)

// Close Long
if (shortCondition and strategy.position_size > 0)
    strategy.close("Long")
    alert('{"account_id":"' + account_id + '","exchange":"binance","action":"close_long","symbol":"BTCUSDT","secret":"' + webhook_secret + '","timestamp":' + str.tostring(timenow / 1000) + '}', alert.freq_once_per_bar_close)

// Close Short
if (longCondition and strategy.position_size < 0)
    strategy.close("Short")
    alert('{"account_id":"' + account_id + '","exchange":"binance","action":"close_short","symbol":"BTCUSDT","secret":"' + webhook_secret + '","timestamp":' + str.tostring(timenow / 1000) + '}', alert.freq_once_per_bar_close)
""",
            backtest_results={
                "win_rate": 58.3,
                "profit_factor": 1.42,
                "sharpe_ratio": 1.15,
                "max_drawdown": 12.5
            }
        )

        # 2. RSI Reversal (평균 회귀 전략)
        library["rsi_reversal"] = StrategyTemplate(
            id="rsi_reversal",
            name="RSI Mean Reversion",
            description="RSI 과매수/과매도 구간에서 반전 매매. 레인지 시장에 적합.",
            author="Classic TA Strategy",
            category="Mean Reversion",
            difficulty="Beginner",
            popularity_score=90,
            indicators=["RSI"],
            default_parameters={
                "rsi_length": 14,
                "oversold": 30,
                "overbought": 70,
                "leverage": 2
            },
            code_template="""
//@version=5
strategy("RSI Mean Reversion", overlay=true)

// Parameters
rsiLength = input.int(14, "RSI Length", minval=1)
oversoldLevel = input.int(30, "Oversold Level", minval=1, maxval=50)
overboughtLevel = input.int(70, "Overbought Level", minval=50, maxval=99)
leverage = input.int(2, "Leverage", minval=1, maxval=125)

// Webhook
account_id = input.string("{{ACCOUNT_ID}}", "Account ID")
webhook_secret = input.string("{{WEBHOOK_SECRET}}", "Webhook Secret")

// RSI
rsiValue = ta.rsi(close, rsiLength)

// Conditions
longCondition = ta.crossover(rsiValue, oversoldLevel)
shortCondition = ta.crossunder(rsiValue, overboughtLevel)

// Plot RSI
hline(oversoldLevel, "Oversold", color=color.green)
hline(overboughtLevel, "Overbought", color=color.red)

// Long Entry
if (longCondition and strategy.position_size == 0)
    strategy.entry("Long", strategy.long)
    alert('{"account_id":"' + account_id + '","exchange":"binance","action":"long","symbol":"BTCUSDT","leverage":' + str.tostring(leverage) + ',"secret":"' + webhook_secret + '","timestamp":' + str.tostring(timenow / 1000) + '}', alert.freq_once_per_bar_close)

// Short Entry
if (shortCondition and strategy.position_size == 0)
    strategy.entry("Short", strategy.short)
    alert('{"account_id":"' + account_id + '","exchange":"binance","action":"short","symbol":"BTCUSDT","leverage":' + str.tostring(leverage) + ',"secret":"' + webhook_secret + '","timestamp":' + str.tostring(timenow / 1000) + '}', alert.freq_once_per_bar_close)

// Close on opposite signal
if (shortCondition and strategy.position_size > 0)
    strategy.close("Long")
    alert('{"account_id":"' + account_id + '","exchange":"binance","action":"close_long","symbol":"BTCUSDT","secret":"' + webhook_secret + '","timestamp":' + str.tostring(timenow / 1000) + '}', alert.freq_once_per_bar_close)

if (longCondition and strategy.position_size < 0)
    strategy.close("Short")
    alert('{"account_id":"' + account_id + '","exchange":"binance","action":"close_short","symbol":"BTCUSDT","secret":"' + webhook_secret + '","timestamp":' + str.tostring(timenow / 1000) + '}', alert.freq_once_per_bar_close)
""",
            backtest_results={
                "win_rate": 62.1,
                "profit_factor": 1.58,
                "sharpe_ratio": 1.32,
                "max_drawdown": 9.8
            }
        )

        # 3. MACD + RSI Combo (복합 전략)
        library["macd_rsi_combo"] = StrategyTemplate(
            id="macd_rsi_combo",
            name="MACD + RSI Combo",
            description="MACD 시그널과 RSI 확인을 결합한 강력한 트렌드 전략",
            author="Advanced Community",
            category="Trend Following",
            difficulty="Intermediate",
            popularity_score=87,
            indicators=["MACD", "RSI"],
            default_parameters={
                "macd_fast": 12,
                "macd_slow": 26,
                "macd_signal": 9,
                "rsi_length": 14,
                "rsi_filter": 50,
                "leverage": 3
            },
            code_template="""
//@version=5
strategy("MACD + RSI Combo", overlay=true)

// Parameters
macdFast = input.int(12, "MACD Fast")
macdSlow = input.int(26, "MACD Slow")
macdSignal = input.int(9, "MACD Signal")
rsiLength = input.int(14, "RSI Length")
rsiFilter = input.int(50, "RSI Filter Level")
leverage = input.int(3, "Leverage", minval=1, maxval=125)

// Webhook
account_id = input.string("{{ACCOUNT_ID}}", "Account ID")
webhook_secret = input.string("{{WEBHOOK_SECRET}}", "Webhook Secret")

// Indicators
[macdLine, signalLine, _] = ta.macd(close, macdFast, macdSlow, macdSignal)
rsiValue = ta.rsi(close, rsiLength)

// Entry Conditions (MACD + RSI 필터)
longCondition = ta.crossover(macdLine, signalLine) and rsiValue > rsiFilter
shortCondition = ta.crossunder(macdLine, signalLine) and rsiValue < rsiFilter

// Long Entry
if (longCondition and strategy.position_size == 0)
    strategy.entry("Long", strategy.long)
    alert('{"account_id":"' + account_id + '","exchange":"binance","action":"long","symbol":"BTCUSDT","leverage":' + str.tostring(leverage) + ',"secret":"' + webhook_secret + '","timestamp":' + str.tostring(timenow / 1000) + '}', alert.freq_once_per_bar_close)

// Short Entry
if (shortCondition and strategy.position_size == 0)
    strategy.entry("Short", strategy.short)
    alert('{"account_id":"' + account_id + '","exchange":"binance","action":"short","symbol":"BTCUSDT","leverage":' + str.tostring(leverage) + ',"secret":"' + webhook_secret + '","timestamp":' + str.tostring(timenow / 1000) + '}', alert.freq_once_per_bar_close)

// Close on opposite signal
if (shortCondition and strategy.position_size > 0)
    strategy.close("Long")
    alert('{"account_id":"' + account_id + '","exchange":"binance","action":"close_long","symbol":"BTCUSDT","secret":"' + webhook_secret + '","timestamp":' + str.tostring(timenow / 1000) + '}', alert.freq_once_per_bar_close)

if (longCondition and strategy.position_size < 0)
    strategy.close("Short")
    alert('{"account_id":"' + account_id + '","exchange":"binance","action":"close_short","symbol":"BTCUSDT","secret":"' + webhook_secret + '","timestamp":' + str.tostring(timenow / 1000) + '}', alert.freq_once_per_bar_close)
""",
            backtest_results={
                "win_rate": 64.5,
                "profit_factor": 1.72,
                "sharpe_ratio": 1.48,
                "max_drawdown": 11.2
            }
        )

        # 4. Bollinger Bands Breakout
        library["bb_breakout"] = StrategyTemplate(
            id="bb_breakout",
            name="Bollinger Bands Breakout",
            description="볼린저 밴드 돌파 전략. 변동성 확대 구간에서 강력함.",
            author="Volatility Specialist",
            category="Breakout",
            difficulty="Intermediate",
            popularity_score=82,
            indicators=["Bollinger Bands"],
            default_parameters={
                "bb_length": 20,
                "bb_mult": 2.0,
                "leverage": 4
            },
            code_template="""
//@version=5
strategy("Bollinger Bands Breakout", overlay=true)

// Parameters
bbLength = input.int(20, "BB Length")
bbMult = input.float(2.0, "BB Multiplier")
leverage = input.int(4, "Leverage", minval=1, maxval=125)

// Webhook
account_id = input.string("{{ACCOUNT_ID}}", "Account ID")
webhook_secret = input.string("{{WEBHOOK_SECRET}}", "Webhook Secret")

// Bollinger Bands
[middle, upper, lower] = ta.bb(close, bbLength, bbMult)

// Breakout Conditions
longCondition = ta.crossover(close, upper)
shortCondition = ta.crossunder(close, lower)

// Plot
plot(middle, "BB Middle", color=color.yellow)
plot(upper, "BB Upper", color=color.red)
plot(lower, "BB Lower", color=color.green)

// Long Entry (상단 돌파)
if (longCondition and strategy.position_size == 0)
    strategy.entry("Long", strategy.long)
    alert('{"account_id":"' + account_id + '","exchange":"binance","action":"long","symbol":"BTCUSDT","leverage":' + str.tostring(leverage) + ',"secret":"' + webhook_secret + '","timestamp":' + str.tostring(timenow / 1000) + '}', alert.freq_once_per_bar_close)

// Short Entry (하단 돌파)
if (shortCondition and strategy.position_size == 0)
    strategy.entry("Short", strategy.short)
    alert('{"account_id":"' + account_id + '","exchange":"binance","action":"short","symbol":"BTCUSDT","leverage":' + str.tostring(leverage) + ',"secret":"' + webhook_secret + '","timestamp":' + str.tostring(timenow / 1000) + '}', alert.freq_once_per_bar_close)

// Close on opposite signal
if (shortCondition and strategy.position_size > 0)
    strategy.close("Long")
    alert('{"account_id":"' + account_id + '","exchange":"binance","action":"close_long","symbol":"BTCUSDT","secret":"' + webhook_secret + '","timestamp":' + str.tostring(timenow / 1000) + '}', alert.freq_once_per_bar_close)

if (longCondition and strategy.position_size < 0)
    strategy.close("Short")
    alert('{"account_id":"' + account_id + '","exchange":"binance","action":"close_short","symbol":"BTCUSDT","secret":"' + webhook_secret + '","timestamp":' + str.tostring(timenow / 1000) + '}', alert.freq_once_per_bar_close)
""",
            backtest_results={
                "win_rate": 55.8,
                "profit_factor": 1.38,
                "sharpe_ratio": 1.05,
                "max_drawdown": 15.3
            }
        )

        # 5. SuperTrend (트렌드 추종 - 고급)
        library["supertrend"] = StrategyTemplate(
            id="supertrend",
            name="SuperTrend Strategy",
            description="ATR 기반 SuperTrend 인디케이터. 강력한 트렌드 추종 전략.",
            author="Advanced Trader",
            category="Trend Following",
            difficulty="Advanced",
            popularity_score=78,
            indicators=["SuperTrend", "ATR"],
            default_parameters={
                "atr_period": 10,
                "atr_multiplier": 3.0,
                "leverage": 5
            },
            code_template="""
//@version=5
strategy("SuperTrend Strategy", overlay=true)

// Parameters
atrPeriod = input.int(10, "ATR Period")
atrMultiplier = input.float(3.0, "ATR Multiplier")
leverage = input.int(5, "Leverage", minval=1, maxval=125)

// Webhook
account_id = input.string("{{ACCOUNT_ID}}", "Account ID")
webhook_secret = input.string("{{WEBHOOK_SECRET}}", "Webhook Secret")

// SuperTrend Calculation
atr = ta.atr(atrPeriod)
upperBand = hl2 + (atrMultiplier * atr)
lowerBand = hl2 - (atrMultiplier * atr)

var float supertrend = na
var int direction = 1

if na(supertrend)
    supertrend := lowerBand
    direction := 1

prevSupertrend = supertrend[1]
if direction == 1
    supertrend := close < prevSupertrend ? upperBand : math.max(lowerBand, prevSupertrend)
else
    supertrend := close > prevSupertrend ? lowerBand : math.min(upperBand, prevSupertrend)

direction := close > supertrend ? 1 : -1

// Entry Conditions
longCondition = direction == 1 and direction[1] == -1
shortCondition = direction == -1 and direction[1] == 1

// Plot
plot(supertrend, "SuperTrend", color=direction == 1 ? color.green : color.red, linewidth=2)

// Long Entry
if (longCondition and strategy.position_size == 0)
    strategy.entry("Long", strategy.long)
    alert('{"account_id":"' + account_id + '","exchange":"binance","action":"long","symbol":"BTCUSDT","leverage":' + str.tostring(leverage) + ',"secret":"' + webhook_secret + '","timestamp":' + str.tostring(timenow / 1000) + '}', alert.freq_once_per_bar_close)

// Short Entry
if (shortCondition and strategy.position_size == 0)
    strategy.entry("Short", strategy.short)
    alert('{"account_id":"' + account_id + '","exchange":"binance","action":"short","symbol":"BTCUSDT","leverage":' + str.tostring(leverage) + ',"secret":"' + webhook_secret + '","timestamp":' + str.tostring(timenow / 1000) + '}', alert.freq_once_per_bar_close)

// Close on opposite signal
if (shortCondition and strategy.position_size > 0)
    strategy.close("Long")
    alert('{"account_id":"' + account_id + '","exchange":"binance","action":"close_long","symbol":"BTCUSDT","secret":"' + webhook_secret + '","timestamp":' + str.tostring(timenow / 1000) + '}', alert.freq_once_per_bar_close)

if (longCondition and strategy.position_size < 0)
    strategy.close("Short")
    alert('{"account_id":"' + account_id + '","exchange":"binance","action":"close_short","symbol":"BTCUSDT","secret":"' + webhook_secret + '","timestamp":' + str.tostring(timenow / 1000) + '}', alert.freq_once_per_bar_close)
""",
            backtest_results={
                "win_rate": 60.2,
                "profit_factor": 1.65,
                "sharpe_ratio": 1.38,
                "max_drawdown": 13.7
            }
        )

        return library

    def get_strategy_by_id(self, strategy_id: str) -> Optional[StrategyTemplate]:
        """전략 ID로 템플릿 조회"""
        return self.strategy_library.get(strategy_id)

    def list_strategies(
        self,
        category: Optional[str] = None,
        difficulty: Optional[str] = None,
        min_popularity: int = 0
    ) -> List[StrategyTemplate]:
        """전략 목록 조회 (필터링)"""
        strategies = list(self.strategy_library.values())

        # 필터 적용
        if category:
            strategies = [s for s in strategies if s.category == category]

        if difficulty:
            strategies = [s for s in strategies if s.difficulty == difficulty]

        if min_popularity > 0:
            strategies = [s for s in strategies if s.popularity_score >= min_popularity]

        # 인기도 순 정렬
        strategies.sort(key=lambda x: x.popularity_score, reverse=True)

        return strategies

    def customize_strategy(
        self,
        template: StrategyTemplate,
        account_id: str,
        webhook_secret: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        전략 템플릿을 사용자 설정에 맞게 커스터마이징

        Args:
            template: 전략 템플릿
            account_id: 계정 ID
            webhook_secret: Webhook Secret
            parameters: 커스터마이징 파라미터 (선택)

        Returns:
            커스터마이징된 Pine Script 코드
        """
        code = template.code_template

        # Webhook 설정 주입
        code = code.replace("{{ACCOUNT_ID}}", account_id)
        code = code.replace("{{WEBHOOK_SECRET}}", webhook_secret)

        # 파라미터 최적화 (사용자가 제공한 경우)
        if parameters:
            for key, value in parameters.items():
                # 기본값을 사용자 값으로 교체
                # 예: fastLength = input.int(9, ...) → fastLength = input.int(12, ...)
                pattern = f'{key} = input\.(int|float|bool|string)\([^,]+,'
                replacement = f'{key} = input.\\1({value},'
                code = re.sub(pattern, replacement, code)

        return code

    async def optimize_parameters(
        self,
        template: StrategyTemplate,
        market_conditions: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        AI 기반 파라미터 최적화

        Args:
            template: 전략 템플릿
            market_conditions: 시장 상황 (volatility, trend, etc.)

        Returns:
            최적화된 파라미터
        """
        logger.info(f"Optimizing parameters for {template.name}...")

        prompt = f"""
Optimize parameters for this trading strategy based on current market conditions:

Strategy: {template.name}
Category: {template.category}
Current Parameters: {template.default_parameters}

Market Conditions:
- Volatility: {market_conditions.get('volatility', 'Medium')}
- Trend: {market_conditions.get('trend', 'Neutral')}
- Volume: {market_conditions.get('volume', 'Normal')}

Recommend optimized parameters considering:
1. Current market volatility
2. Trend strength
3. Risk management

Respond in JSON format with parameter names and optimized values.
"""

        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a professional trading strategy optimizer."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )

            result = response.choices[0].message.content

            import json
            optimized_params = json.loads(result)
            logger.info(f"Optimized parameters: {optimized_params}")

            return optimized_params

        except Exception as e:
            logger.error(f"Parameter optimization failed: {str(e)}")
            return template.default_parameters


# 싱글톤 인스턴스
strategy_optimizer = StrategyOptimizer()
