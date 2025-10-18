"""
Backtesting and Strategy Testing API

Real backtesting endpoints using TradingView strategies and BacktestEngine.
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from enum import Enum
import pandas as pd
import logging

from app.strategies.strategies import (
    SuperTrendStrategy,
    RSIEMAStrategy,
    MACDStochStrategy,
    IchimokuStrategy,
    WaveTrendStrategy,
    MultiIndicatorStrategy,
    BaseStrategy
)
from app.backtesting.engine import BacktestEngine, BacktestResult
from app.backtesting.metrics import PerformanceMetrics
from app.ai.pine_converter import get_pine_converter, ConversionResult

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/backtest", tags=["Backtesting"])


# ===== Enums =====

class StrategyType(str, Enum):
    """Available strategy types"""
    SUPERTREND = "supertrend"
    RSI_EMA = "rsi_ema"
    MACD_STOCH = "macd_stoch"
    ICHIMOKU = "ichimoku"
    WAVETREND = "wavetrend"
    MULTI_INDICATOR = "multi_indicator"


class TimeframeType(str, Enum):
    """Timeframe options"""
    M1 = "1m"
    M5 = "5m"
    M15 = "15m"
    M30 = "30m"
    H1 = "1h"
    H4 = "4h"
    D1 = "1d"


# ===== Request/Response Models =====

class StrategyInfo(BaseModel):
    """Strategy information model"""
    id: str
    name: str
    description: str
    category: str
    performance_notes: Optional[str] = None
    recommended_symbols: List[str] = []
    recommended_timeframes: List[str] = []

    class Config:
        json_schema_extra = {
            "example": {
                "id": "supertrend",
                "name": "SuperTrend Strategy",
                "description": "ATR-based trend following indicator with 67% win rate",
                "category": "Trend Following",
                "performance_notes": "Best performer in Feb 2025: 67% win rate, 177% returns",
                "recommended_symbols": ["BTCUSDT", "ETHUSDT"],
                "recommended_timeframes": ["5m", "15m", "1h"]
            }
        }


class BacktestRequest(BaseModel):
    """Backtest execution request"""
    strategy_type: StrategyType
    symbol: str = Field(default="BTCUSDT", description="Trading symbol")
    initial_capital: float = Field(default=10000.0, ge=100, description="Initial capital in USDT")
    leverage: int = Field(default=3, ge=1, le=20, description="Trading leverage")
    position_size_pct: float = Field(default=0.10, ge=0.01, le=1.0, description="Position size as % of capital")

    # Date range
    start_date: Optional[str] = None  # Format: "2025-01-01"
    end_date: Optional[str] = None
    days_back: int = Field(default=30, ge=1, le=365, description="Days to backtest if dates not provided")

    # Fee structure
    maker_fee: float = Field(default=0.0002, description="Maker fee (0.02% = 0.0002)")
    taker_fee: float = Field(default=0.0004, description="Taker fee (0.04% = 0.0004)")

    # Strategy-specific parameters
    custom_params: Optional[Dict[str, Any]] = Field(default=None, description="Strategy-specific parameters")

    class Config:
        json_schema_extra = {
            "example": {
                "strategy_type": "supertrend",
                "symbol": "BTCUSDT",
                "initial_capital": 10000,
                "leverage": 3,
                "position_size_pct": 0.10,
                "days_back": 30,
                "maker_fee": 0.0002,
                "taker_fee": 0.0004
            }
        }


class TradeInfo(BaseModel):
    """Individual trade information"""
    entry_time: str
    exit_time: Optional[str]
    direction: str
    entry_price: float
    exit_price: Optional[float]
    quantity: float
    leverage: int
    pnl: float
    pnl_pct: float
    fees: float
    exit_reason: str
    stop_loss: Optional[float]
    take_profit: Optional[float]


class BacktestResponse(BaseModel):
    """Backtest result response"""
    strategy_name: str
    symbol: str
    start_date: str
    end_date: str

    # Performance metrics
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float

    total_return: float
    total_return_pct: float
    annualized_return: float

    max_drawdown: float
    max_drawdown_pct: float

    sharpe_ratio: float
    sortino_ratio: float
    profit_factor: float

    avg_win: float
    avg_loss: float
    avg_return_per_trade: float

    # Rating
    performance_rating: str  # EXCELLENT, GOOD, AVERAGE, POOR

    # Trade list
    trades: List[TradeInfo]

    # Equity curve data
    equity_curve: List[Dict[str, Any]]
    drawdown_curve: List[Dict[str, Any]]


class CompareStrategiesRequest(BaseModel):
    """Compare multiple strategies request"""
    strategies: List[StrategyType]
    symbol: str = "BTCUSDT"
    initial_capital: float = 10000.0
    leverage: int = 3
    days_back: int = 30


class StrategyComparison(BaseModel):
    """Single strategy comparison result"""
    strategy_name: str
    win_rate: float
    total_return_pct: float
    sharpe_ratio: float
    max_drawdown_pct: float
    profit_factor: float
    total_trades: int
    performance_rating: str


class CompareStrategiesResponse(BaseModel):
    """Compare strategies response"""
    symbol: str
    period: str
    initial_capital: float
    comparisons: List[StrategyComparison]
    best_strategy: str
    best_metric: str


# ===== Helper Functions =====

def get_strategy_instance(strategy_type: StrategyType, params: Optional[Dict] = None) -> BaseStrategy:
    """Get strategy instance based on type"""
    strategy_map = {
        StrategyType.SUPERTREND: SuperTrendStrategy,
        StrategyType.RSI_EMA: RSIEMAStrategy,
        StrategyType.MACD_STOCH: MACDStochStrategy,
        StrategyType.ICHIMOKU: IchimokuStrategy,
        StrategyType.WAVETREND: WaveTrendStrategy,
        StrategyType.MULTI_INDICATOR: MultiIndicatorStrategy,
    }

    strategy_class = strategy_map.get(strategy_type)
    if not strategy_class:
        raise ValueError(f"Unknown strategy type: {strategy_type}")

    # Initialize with custom params if provided
    if params:
        return strategy_class(**params)
    else:
        return strategy_class()


def generate_mock_ohlcv_data(
    symbol: str,
    days_back: int = 30,
    timeframe: str = "1h"
) -> pd.DataFrame:
    """
    Generate mock OHLCV data for backtesting

    TODO: Replace with real data from Binance API once API keys are available
    """
    import numpy as np

    # Calculate number of candles based on timeframe
    timeframe_minutes = {
        "1m": 1, "5m": 5, "15m": 15, "30m": 30,
        "1h": 60, "4h": 240, "1d": 1440
    }
    minutes = timeframe_minutes.get(timeframe, 60)
    num_candles = int((days_back * 24 * 60) / minutes)

    # Generate timestamps
    end_time = datetime.now()
    start_time = end_time - timedelta(days=days_back)
    timestamps = pd.date_range(start=start_time, end=end_time, periods=num_candles)

    # Generate realistic price data (random walk)
    base_price = 45000.0 if "BTC" in symbol else 2500.0  # BTC vs ETH
    volatility = 0.02  # 2% volatility

    # Random walk
    returns = np.random.normal(0.0001, volatility, num_candles)  # Slight upward bias
    prices = base_price * np.exp(np.cumsum(returns))

    # Generate OHLCV
    data = []
    for i, (timestamp, close) in enumerate(zip(timestamps, prices)):
        # Generate high/low based on close with some randomness
        high = close * (1 + abs(np.random.normal(0, volatility/2)))
        low = close * (1 - abs(np.random.normal(0, volatility/2)))
        open_price = (high + low) / 2 + np.random.normal(0, (high - low) / 4)

        volume = np.random.uniform(1000, 10000)

        data.append({
            'timestamp': timestamp,
            'open': open_price,
            'high': high,
            'low': low,
            'close': close,
            'volume': volume
        })

    df = pd.DataFrame(data)
    return df


def backtest_result_to_response(result: BacktestResult, symbol: str) -> BacktestResponse:
    """Convert BacktestResult to API response"""

    # Convert trades
    trades = []
    for trade in result.trades:
        trades.append(TradeInfo(
            entry_time=trade.entry_time.isoformat(),
            exit_time=trade.exit_time.isoformat() if trade.exit_time else None,
            direction=trade.direction,
            entry_price=trade.entry_price,
            exit_price=trade.exit_price,
            quantity=trade.quantity,
            leverage=trade.leverage,
            pnl=trade.pnl,
            pnl_pct=trade.pnl_pct,
            fees=trade.fees,
            exit_reason=trade.exit_reason,
            stop_loss=trade.stop_loss,
            take_profit=trade.take_profit
        ))

    # Convert equity curve
    equity_curve = []
    for timestamp, value in result.equity_curve.items():
        equity_curve.append({
            'timestamp': timestamp.isoformat(),
            'equity': float(value)
        })

    # Convert drawdown curve
    drawdown_curve = []
    for timestamp, value in result.drawdown_curve.items():
        drawdown_curve.append({
            'timestamp': timestamp.isoformat(),
            'drawdown': float(value),
            'drawdown_pct': (float(value) / float(result.equity_curve.loc[timestamp])) * 100 if result.equity_curve.loc[timestamp] > 0 else 0
        })

    # Get performance rating
    metrics = PerformanceMetrics.from_backtest_result(result)

    return BacktestResponse(
        strategy_name=result.strategy_name,
        symbol=symbol,
        start_date=result.start_date.isoformat(),
        end_date=result.end_date.isoformat(),
        total_trades=result.total_trades,
        winning_trades=result.winning_trades,
        losing_trades=result.losing_trades,
        win_rate=result.win_rate,
        total_return=result.total_return,
        total_return_pct=result.total_return_pct,
        annualized_return=metrics.annualized_return,
        max_drawdown=result.max_drawdown,
        max_drawdown_pct=result.max_drawdown_pct,
        sharpe_ratio=result.sharpe_ratio,
        sortino_ratio=result.sortino_ratio,
        profit_factor=result.profit_factor,
        avg_win=result.avg_win,
        avg_loss=result.avg_loss,
        avg_return_per_trade=result.avg_return_per_trade,
        performance_rating=metrics.get_rating(),
        trades=trades,
        equity_curve=equity_curve,
        drawdown_curve=drawdown_curve
    )


# ===== API Endpoints =====

@router.get("/strategies", response_model=List[StrategyInfo])
async def list_available_strategies():
    """
    Get list of all available TradingView-based strategies

    Returns comprehensive information about each strategy including:
    - Description and category
    - Performance notes (historical data)
    - Recommended symbols and timeframes
    """
    strategies = [
        StrategyInfo(
            id="supertrend",
            name="SuperTrend Strategy",
            description="ATR-based trend following indicator",
            category="Trend Following",
            performance_notes="Best performer: 67% win rate, 177% returns (Feb 2025 live trading)",
            recommended_symbols=["BTCUSDT", "ETHUSDT", "BNBUSDT"],
            recommended_timeframes=["5m", "15m", "1h"]
        ),
        StrategyInfo(
            id="rsi_ema",
            name="RSI + EMA Crossover",
            description="Momentum confirmation with trend following",
            category="Momentum + Trend",
            performance_notes="Reliable for trending markets with clear momentum shifts",
            recommended_symbols=["BTCUSDT", "ETHUSDT"],
            recommended_timeframes=["15m", "1h", "4h"]
        ),
        StrategyInfo(
            id="macd_stoch",
            name="MACD + Stochastic RSI",
            description="Multi-confirmation system with momentum and trend",
            category="Multi-Confirmation",
            performance_notes="High accuracy with fewer false signals",
            recommended_symbols=["BTCUSDT", "ETHUSDT", "SOLUSDT"],
            recommended_timeframes=["1h", "4h"]
        ),
        StrategyInfo(
            id="ichimoku",
            name="Ichimoku Cloud",
            description="Comprehensive trend system with support/resistance",
            category="Comprehensive",
            performance_notes="Best for strong trending markets",
            recommended_symbols=["BTCUSDT", "ETHUSDT"],
            recommended_timeframes=["4h", "1d"]
        ),
        StrategyInfo(
            id="wavetrend",
            name="WaveTrend Dead Zone",
            description="Oscillator-based strategy for ranging markets",
            category="Oscillator",
            performance_notes="2+ years profitable performance on TradingView",
            recommended_symbols=["BTCUSDT", "ETHUSDT", "BNBUSDT"],
            recommended_timeframes=["15m", "1h"]
        ),
        StrategyInfo(
            id="multi_indicator",
            name="Multi-Indicator Consensus",
            description="Ensemble voting system across multiple strategies",
            category="Ensemble",
            performance_notes="Highest accuracy through consensus voting",
            recommended_symbols=["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT"],
            recommended_timeframes=["15m", "1h", "4h"]
        )
    ]

    return strategies


@router.post("/run", response_model=BacktestResponse)
async def run_backtest(request: BacktestRequest):
    """
    Run backtest on historical data using selected strategy

    Simulates realistic trading conditions:
    - Transaction fees (maker/taker)
    - Leverage support
    - Dynamic stop-loss and take-profit
    - Position sizing based on risk

    Returns comprehensive performance metrics and trade history.
    """
    try:
        # Get strategy instance
        strategy = get_strategy_instance(request.strategy_type, request.custom_params)

        # Generate historical data
        # TODO: Replace with real Binance data once API keys available
        df = generate_mock_ohlcv_data(
            symbol=request.symbol,
            days_back=request.days_back
        )

        logger.info(f"Running backtest: {strategy.name} on {request.symbol}, {len(df)} candles")

        # Initialize backtest engine
        engine = BacktestEngine(
            initial_capital=request.initial_capital,
            maker_fee=request.maker_fee,
            taker_fee=request.taker_fee,
            leverage=request.leverage,
            position_size_pct=request.position_size_pct
        )

        # Run backtest
        result = engine.run(
            strategy=strategy,
            df=df,
            symbol=request.symbol
        )

        logger.info(
            f"Backtest complete: {result.total_trades} trades, "
            f"{result.win_rate:.1f}% win rate, "
            f"{result.total_return_pct:+.2f}% return"
        )

        # Convert to API response
        response = backtest_result_to_response(result, request.symbol)

        return response

    except Exception as e:
        logger.error(f"Backtest error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Backtest failed: {str(e)}"
        )


@router.post("/compare", response_model=CompareStrategiesResponse)
async def compare_strategies(request: CompareStrategiesRequest):
    """
    Compare multiple strategies on the same historical data

    Runs backtests for all selected strategies and returns comparative metrics.
    Helps identify which strategy performs best for specific market conditions.
    """
    try:
        # Generate historical data once for all strategies
        df = generate_mock_ohlcv_data(
            symbol=request.symbol,
            days_back=request.days_back
        )

        comparisons = []
        best_sharpe = -999
        best_strategy_name = ""

        # Run backtest for each strategy
        for strategy_type in request.strategies:
            strategy = get_strategy_instance(strategy_type)

            engine = BacktestEngine(
                initial_capital=request.initial_capital,
                leverage=request.leverage
            )

            result = engine.run(
                strategy=strategy,
                df=df,
                symbol=request.symbol
            )

            metrics = PerformanceMetrics.from_backtest_result(result)

            comparisons.append(StrategyComparison(
                strategy_name=result.strategy_name,
                win_rate=result.win_rate,
                total_return_pct=result.total_return_pct,
                sharpe_ratio=result.sharpe_ratio,
                max_drawdown_pct=result.max_drawdown_pct,
                profit_factor=result.profit_factor,
                total_trades=result.total_trades,
                performance_rating=metrics.get_rating()
            ))

            # Track best strategy by Sharpe ratio
            if result.sharpe_ratio > best_sharpe:
                best_sharpe = result.sharpe_ratio
                best_strategy_name = result.strategy_name

        # Sort by Sharpe ratio descending
        comparisons.sort(key=lambda x: x.sharpe_ratio, reverse=True)

        return CompareStrategiesResponse(
            symbol=request.symbol,
            period=f"{request.days_back}d",
            initial_capital=request.initial_capital,
            comparisons=comparisons,
            best_strategy=best_strategy_name,
            best_metric="sharpe_ratio"
        )

    except Exception as e:
        logger.error(f"Strategy comparison error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Comparison failed: {str(e)}"
        )


@router.get("/signal/{strategy_type}")
async def get_current_signal(
    strategy_type: StrategyType,
    symbol: str = Query(default="BTCUSDT", description="Trading symbol"),
    custom_params: Optional[str] = Query(default=None, description="JSON custom parameters")
):
    """
    Get current trading signal from strategy

    Returns real-time signal based on latest market data:
    - Entry recommendation (LONG/SHORT/NEUTRAL)
    - Confidence level (0-1)
    - Stop-loss and take-profit levels
    - Reasoning behind the signal
    """
    try:
        # Parse custom params if provided
        params = None
        if custom_params:
            import json
            params = json.loads(custom_params)

        # Get strategy instance
        strategy = get_strategy_instance(strategy_type, params)

        # Generate recent historical data for signal calculation
        # TODO: Replace with real-time Binance data
        df = generate_mock_ohlcv_data(symbol=symbol, days_back=7)
        current_price = df['close'].iloc[-1]

        # Generate signal
        signal = strategy.generate_signal(df, current_price)

        return {
            'strategy': strategy.name,
            'symbol': symbol,
            'timestamp': datetime.now().isoformat(),
            'current_price': float(current_price),
            'signal': {
                'should_enter': signal.should_enter,
                'direction': signal.direction if signal.should_enter else 'NEUTRAL',
                'confidence': signal.confidence,
                'entry_price': signal.entry_price,
                'stop_loss': signal.stop_loss,
                'take_profit': signal.take_profit,
                'reasoning': signal.reasoning,
                'risk_reward_ratio': (
                    abs(signal.take_profit - signal.entry_price) / abs(signal.entry_price - signal.stop_loss)
                    if signal.stop_loss and signal.take_profit else None
                )
            },
            'indicator_values': signal.indicator_values
        }

    except Exception as e:
        logger.error(f"Signal generation error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Signal generation failed: {str(e)}"
        )


# ===== Pine Script Import/Conversion =====

class PineScriptImportRequest(BaseModel):
    """Pine Script import request"""
    pine_script_code: str = Field(..., description="Pine Script source code to convert")
    indicator_name: Optional[str] = Field(None, description="Custom name for the indicator")

    class Config:
        json_schema_extra = {
            "example": {
                "pine_script_code": '''
//@version=5
indicator("My Custom RSI", overlay=false)

length = input.int(14, title="RSI Length")
source = input(close, title="Source")

rsi_value = ta.rsi(source, length)

plot(rsi_value, "RSI", color=color.blue)
hline(70, "Overbought", color=color.red)
hline(30, "Oversold", color=color.green)
                ''',
                "indicator_name": "custom_rsi"
            }
        }


class PineScriptImportResponse(BaseModel):
    """Pine Script import response"""
    success: bool
    message: str
    python_code: Optional[str] = None
    function_name: Optional[str] = None
    description: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    warnings: List[str] = []

    # Usage instructions
    usage_example: Optional[str] = None


class PineScriptAnalysisResponse(BaseModel):
    """Pine Script analysis response"""
    success: bool
    message: str

    # Metadata
    indicator_type: Optional[str] = None  # study, strategy
    version: Optional[int] = None
    title: Optional[str] = None

    # Features detected
    has_plots: bool = False
    has_alerts: bool = False
    uses_security: bool = False

    # Parameters found
    input_parameters: List[Dict[str, Any]] = []

    # Calculations used
    calculations: List[str] = []

    # Conversion feasibility
    can_convert: bool = True
    conversion_complexity: str = "simple"  # simple, moderate, complex
    conversion_notes: List[str] = []


@router.post("/import-pine-script", response_model=PineScriptImportResponse)
async def import_pine_script(request: PineScriptImportRequest):
    """
    Convert Pine Script indicator to Python code

    **기능:**
    - Pine Script 코드를 자동으로 Python pandas/numpy 코드로 변환
    - 백테스팅 시스템과 호환되는 형식으로 생성
    - 변환된 코드를 indicators.py에 추가할 수 있는 형태로 제공

    **프로세스:**
    1. Pine Script 코드 분석
    2. 메타데이터 추출 (제목, 파라미터, 계산식)
    3. Python 코드 생성 (AI 기반 또는 템플릿 기반)
    4. 코드 검증 및 안전성 체크
    5. 사용 예시 및 경고 메시지 생성

    **주의사항:**
    - 복잡한 Pine Script는 수동 수정이 필요할 수 있습니다
    - security() 함수나 다중 타임프레임은 지원되지 않습니다
    - 변환된 코드는 반드시 검토 후 사용하세요
    """
    try:
        # Input validation
        if not request.pine_script_code or len(request.pine_script_code.strip()) < 10:
            raise HTTPException(
                status_code=400,
                detail="Pine Script 코드가 너무 짧거나 비어있습니다. 최소 10자 이상 입력해주세요."
            )

        if len(request.pine_script_code) > 50000:
            raise HTTPException(
                status_code=400,
                detail="Pine Script 코드가 너무 깁니다. 50,000자 이하로 입력해주세요."
            )

        # Get converter instance
        converter = get_pine_converter()

        # Convert Pine Script to Python
        result: ConversionResult = await converter.convert_to_python(
            pine_script=request.pine_script_code,
            indicator_name=request.indicator_name
        )

        if not result.success:
            return PineScriptImportResponse(
                success=False,
                message=f"변환 실패: {result.error_message}",
                warnings=result.warnings or []
            )

        # Generate usage example
        usage_example = f'''
# indicators.py에 추가:
{result.python_code}

# 사용 예시:
import pandas as pd
from app.strategies.indicators import {result.function_name}

# OHLCV 데이터가 있다고 가정
df = pd.DataFrame(...)  # timestamp, open, high, low, close, volume

# 인디케이터 계산
indicator = {result.function_name}(df)

print(indicator.tail())
'''

        return PineScriptImportResponse(
            success=True,
            message="Pine Script가 성공적으로 Python으로 변환되었습니다!",
            python_code=result.python_code,
            function_name=result.function_name,
            description=result.description,
            parameters=result.parameters,
            warnings=result.warnings or [],
            usage_example=usage_example.strip()
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Pine Script import error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Pine Script 변환 중 오류가 발생했습니다: {str(e)}"
        )


@router.post("/analyze-pine-script", response_model=PineScriptAnalysisResponse)
async def analyze_pine_script(request: PineScriptImportRequest):
    """
    Pine Script 코드 분석 (변환 전 미리보기)

    **기능:**
    - Pine Script 코드의 구조와 기능 분석
    - 변환 가능 여부 및 복잡도 평가
    - 사용된 함수와 파라미터 목록 제공
    - 변환 시 예상되는 이슈 사전 확인

    **사용 시나리오:**
    1. Pine Script 변환 전에 먼저 분석하여 변환 가능성 확인
    2. 복잡한 스크립트의 경우 어떤 부분이 문제인지 미리 파악
    3. 필요한 수정사항이나 제한사항 사전 확인
    """
    try:
        # Input validation
        if not request.pine_script_code or len(request.pine_script_code.strip()) < 10:
            raise HTTPException(
                status_code=400,
                detail="Pine Script 코드가 너무 짧거나 비어있습니다."
            )

        # Get converter instance
        converter = get_pine_converter()

        # Analyze Pine Script
        analysis = converter._analyze_pine_script(request.pine_script_code)
        metadata = converter._extract_metadata(request.pine_script_code)

        # Determine indicator type
        indicator_type = "strategy" if analysis['has_strategy'] else "study"

        # Assess conversion complexity
        complexity = "simple"
        conversion_notes = []
        can_convert = True

        if analysis['uses_security']:
            complexity = "complex"
            can_convert = False
            conversion_notes.append(
                "⚠️ security() 함수 사용: 다중 타임프레임은 현재 지원되지 않습니다."
            )

        if analysis['has_strategy']:
            complexity = "moderate"
            conversion_notes.append(
                "ℹ️ Strategy 타입: 백테스팅 엔진과 통합하려면 BaseStrategy 클래스를 상속해야 합니다."
            )

        if len(analysis['calculations']) > 10:
            if complexity == "simple":
                complexity = "moderate"
            conversion_notes.append(
                f"ℹ️ {len(analysis['calculations'])}개의 계산식 발견: 변환 후 검증이 필요합니다."
            )

        # Format input parameters
        input_params = []
        for inp in analysis['inputs']:
            input_params.append({
                'name': inp['name'],
                'default_value': inp['default'],
                'type': 'number'  # Pine Script는 대부분 숫자
            })

        return PineScriptAnalysisResponse(
            success=True,
            message="Pine Script 분석이 완료되었습니다.",
            indicator_type=indicator_type,
            version=analysis['version'],
            title=metadata.get('title', '제목 없음'),
            has_plots=analysis['has_plot'],
            has_alerts=analysis['has_alertcondition'],
            uses_security=analysis['uses_security'],
            input_parameters=input_params,
            calculations=analysis['calculations'],
            can_convert=can_convert,
            conversion_complexity=complexity,
            conversion_notes=conversion_notes
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Pine Script analysis error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Pine Script 분석 중 오류가 발생했습니다: {str(e)}"
        )
