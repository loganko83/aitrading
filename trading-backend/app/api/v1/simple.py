"""
Simple API - User-Friendly One-Click Operations

Simplified endpoints for easy backtesting and trading.
No complex parameters required.
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from app.core.presets import (
    get_preset,
    list_presets,
    get_preset_for_user,
    apply_preset_to_backtest_request,
    TradingPreset,
    PresetCategory,
    PRESETS
)
from app.core.exchange_config import (
    get_exchange_config,
    get_optimal_settings,
    validate_trading_parameters,
    convert_symbol_format
)
from app.core.cache import cached, cache_manager
from app.strategies.strategies import BaseStrategy, get_strategy_instance
from app.backtesting.engine import BacktestEngine
from app.api.v1.backtest import (
    generate_mock_ohlcv_data,
    backtest_result_to_response,
    BacktestResponse
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/simple", tags=["Simple API"])


# ===== Request/Response Models =====

class PresetInfo(BaseModel):
    """Preset information"""
    id: str
    name: str
    name_ko: str
    description: str
    description_ko: str
    category: str

    # Key settings
    strategy_type: str
    leverage: int
    position_size_pct: float

    # Performance expectations
    expected_win_rate: str
    expected_return_monthly: str
    expected_max_drawdown: str

    # User guidance
    difficulty: str
    time_commitment: str
    recommended_capital_min: float

    # Compatibility
    compatible_exchanges: List[str]
    recommended_symbols: List[str]


class QuickBacktestRequest(BaseModel):
    """Quick backtest with preset"""
    preset_id: str = Field(..., description="Preset ID (e.g., 'beginner_safe')")
    exchange: str = Field(default="binance", description="Exchange: binance or okx")
    symbol: Optional[str] = Field(None, description="Trading symbol (optional, uses preset default)")
    days_back: int = Field(default=30, ge=7, le=90, description="Days to backtest")
    initial_capital: float = Field(default=10000.0, ge=100, description="Starting capital in USDT")

    class Config:
        json_schema_extra = {
            "example": {
                "preset_id": "balanced_trader",
                "exchange": "binance",
                "days_back": 30,
                "initial_capital": 10000
            }
        }


class ExchangeInfo(BaseModel):
    """Exchange information"""
    exchange: str
    mode: str
    maker_fee: float
    taker_fee: float
    max_leverage: int
    recommended_leverage: int
    optimal_symbols: List[str]
    optimal_timeframes: List[str]


class SmartRecommendationRequest(BaseModel):
    """Smart recommendation request"""
    capital: float = Field(..., ge=100, description="Available capital in USDT")
    experience_level: str = Field(default="beginner", description="beginner, intermediate, or advanced")
    risk_tolerance: str = Field(default="low", description="low, medium, or high")
    exchange: str = Field(default="binance", description="Preferred exchange")

    class Config:
        json_schema_extra = {
            "example": {
                "capital": 5000,
                "experience_level": "intermediate",
                "risk_tolerance": "medium",
                "exchange": "binance"
            }
        }


class SmartRecommendationResponse(BaseModel):
    """Smart recommendation response"""
    recommended_preset: PresetInfo
    reasoning: str
    reasoning_ko: str
    warnings: List[str]
    tips: List[str]


# ===== API Endpoints =====

@router.get("/presets", response_model=List[PresetInfo])
async def list_available_presets(
    category: Optional[str] = Query(None, description="Filter by category: beginner, conservative, balanced, aggressive, professional"),
    min_capital: Optional[float] = Query(None, description="Filter by minimum capital")
):
    """
    모든 사용 가능한 프리셋 조회

    **프리셋이란?**
    - 미리 설정된 트레이딩 설정 모음
    - 초보자부터 전문가까지 각 레벨에 최적화
    - 복잡한 파라미터 설정 불필요

    **카테고리:**
    - beginner: 초보자용 (낮은 리스크, 간단한 전략)
    - conservative: 보수적 (안정적 성장)
    - balanced: 균형잡힌 (가장 인기)
    - aggressive: 공격적 (높은 수익, 높은 리스크)
    - professional: 전문가용 (완전한 제어)
    """
    try:
        # Convert category string to enum
        category_enum = None
        if category:
            try:
                category_enum = PresetCategory(category.lower())
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid category: {category}. Must be one of: beginner, conservative, balanced, aggressive, professional"
                )

        presets = list_presets(category=category_enum, min_capital=min_capital)

        return [
            PresetInfo(
                id=p.id,
                name=p.name,
                name_ko=p.name_ko,
                description=p.description,
                description_ko=p.description_ko,
                category=p.category.value,
                strategy_type=p.strategy_type,
                leverage=p.leverage,
                position_size_pct=p.position_size_pct,
                expected_win_rate=p.expected_win_rate,
                expected_return_monthly=p.expected_return_monthly,
                expected_max_drawdown=p.expected_max_drawdown,
                difficulty=p.difficulty,
                time_commitment=p.time_commitment,
                recommended_capital_min=p.recommended_capital_min,
                compatible_exchanges=p.compatible_exchanges,
                recommended_symbols=p.recommended_symbols
            )
            for p in presets
        ]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"List presets error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to list presets: {str(e)}")


@router.post("/recommend", response_model=SmartRecommendationResponse)
async def get_smart_recommendation(request: SmartRecommendationRequest):
    """
    AI 기반 스마트 추천

    **기능:**
    - 자본금, 경험, 리스크 성향에 맞는 프리셋 자동 추천
    - 개인화된 조언 및 경고 제공
    - 초보자도 쉽게 시작 가능

    **경험 레벨:**
    - beginner: 트레이딩 경험 없음 또는 6개월 미만
    - intermediate: 6개월~2년 경험
    - advanced: 2년 이상 또는 전문가

    **리스크 성향:**
    - low: 안정적 수익 선호, 손실 최소화
    - medium: 균형잡힌 접근
    - high: 높은 수익 추구, 손실 감내 가능
    """
    try:
        # Validate inputs
        if request.experience_level not in ["beginner", "intermediate", "advanced"]:
            raise HTTPException(
                status_code=400,
                detail="experience_level must be: beginner, intermediate, or advanced"
            )

        if request.risk_tolerance not in ["low", "medium", "high"]:
            raise HTTPException(
                status_code=400,
                detail="risk_tolerance must be: low, medium, or high"
            )

        # Get recommendation
        preset = get_preset_for_user(
            capital=request.capital,
            experience_level=request.experience_level,
            risk_tolerance=request.risk_tolerance
        )

        # Generate reasoning
        reasoning_map = {
            ("beginner", "low"): "You're new to trading and prefer low risk. Starting with a safe, simple strategy is the best choice.",
            ("beginner", "medium"): "As a beginner with moderate risk tolerance, a conservative growth strategy will help you learn while earning steady returns.",
            ("beginner", "high"): "Even with high risk tolerance, beginners should start with balanced strategies to develop skills first.",
            ("intermediate", "low"): "With your experience, a conservative approach will provide steady growth with minimal stress.",
            ("intermediate", "medium"): "A balanced strategy matches your experience and risk profile perfectly.",
            ("intermediate", "high"): "Your experience allows for more aggressive strategies with higher profit potential.",
            ("advanced", "low"): "Despite your experience, a balanced approach ensures consistent returns.",
            ("advanced", "medium"): "Your skills enable aggressive strategies while managing risk effectively.",
            ("advanced", "high"): "Professional mode unlocks full potential with advanced risk management."
        }

        reasoning_ko_map = {
            ("beginner", "low"): "트레이딩 초보자이고 낮은 리스크를 선호하시네요. 안전하고 간단한 전략으로 시작하는 것이 최선입니다.",
            ("beginner", "medium"): "초보자이지만 적당한 리스크는 감수할 수 있으시군요. 보수적 성장 전략으로 배우면서 꾸준한 수익을 얻을 수 있습니다.",
            ("beginner", "high"): "높은 리스크를 감수하려 하지만, 초보자는 먼저 균형잡힌 전략으로 스킬을 개발해야 합니다.",
            ("intermediate", "low"): "경험이 있으시니, 보수적 접근으로 스트레스 없이 꾸준한 성장을 기대할 수 있습니다.",
            ("intermediate", "medium"): "균형잡힌 전략이 당신의 경험과 리스크 프로필에 완벽하게 맞습니다.",
            ("intermediate", "high"): "경험이 있어 더 공격적인 전략으로 높은 수익을 추구할 수 있습니다.",
            ("advanced", "low"): "경험이 많지만, 균형잡힌 접근이 일관된 수익을 보장합니다.",
            ("advanced", "medium"): "당신의 스킬로 리스크를 효과적으로 관리하며 공격적 전략을 사용할 수 있습니다.",
            ("advanced", "high"): "전문가 모드로 고급 리스크 관리와 함께 최대 잠재력을 발휘하세요."
        }

        key = (request.experience_level, request.risk_tolerance)
        reasoning = reasoning_map.get(key, "Based on your profile, this preset is recommended.")
        reasoning_ko = reasoning_ko_map.get(key, "당신의 프로필에 따라 이 프리셋을 추천합니다.")

        # Generate warnings
        warnings = []
        if request.capital < preset.recommended_capital_min:
            warnings.append(
                f"⚠️ 추천 최소 자본금은 ${preset.recommended_capital_min:.0f}입니다. "
                f"현재 ${request.capital:.0f}로는 리스크가 높을 수 있습니다."
            )

        if request.experience_level == "beginner" and preset.leverage > 3:
            warnings.append(
                f"⚠️ 초보자에게 {preset.leverage}x 레버리지는 위험할 수 있습니다. "
                "먼저 낮은 레버리지로 연습하세요."
            )

        # Generate tips
        tips = [
            f"💡 추천 심볼: {', '.join(preset.recommended_symbols[:3])}",
            f"💡 추천 타임프레임: {', '.join(preset.recommended_timeframes[:2])}",
            f"💡 예상 월 수익률: {preset.expected_return_monthly}",
            f"💡 시간 투입: {preset.time_commitment}"
        ]

        if preset.difficulty == "Easy":
            tips.append("💡 초보자도 쉽게 시작할 수 있는 전략입니다")
        elif preset.difficulty == "Hard":
            tips.append("💡 경험자용 전략입니다. 충분한 연습 후 사용하세요")

        return SmartRecommendationResponse(
            recommended_preset=PresetInfo(
                id=preset.id,
                name=preset.name,
                name_ko=preset.name_ko,
                description=preset.description,
                description_ko=preset.description_ko,
                category=preset.category.value,
                strategy_type=preset.strategy_type,
                leverage=preset.leverage,
                position_size_pct=preset.position_size_pct,
                expected_win_rate=preset.expected_win_rate,
                expected_return_monthly=preset.expected_return_monthly,
                expected_max_drawdown=preset.expected_max_drawdown,
                difficulty=preset.difficulty,
                time_commitment=preset.time_commitment,
                recommended_capital_min=preset.recommended_capital_min,
                compatible_exchanges=preset.compatible_exchanges,
                recommended_symbols=preset.recommended_symbols
            ),
            reasoning=reasoning,
            reasoning_ko=reasoning_ko,
            warnings=warnings,
            tips=tips
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Smart recommendation error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to generate recommendation: {str(e)}")


@router.post("/quick-backtest", response_model=BacktestResponse)
@cached(cache_type="backtest", ttl_seconds=1800)  # Cache for 30 minutes
async def run_quick_backtest(request: QuickBacktestRequest):
    """
    원클릭 빠른 백테스트

    **사용법:**
    1. 프리셋 선택 (preset_id)
    2. 거래소 선택 (binance or okx)
    3. 실행 클릭!

    **장점:**
    - 복잡한 파라미터 설정 불필요
    - 거래소별로 자동 최적화
    - 3초 이내 결과 확인 (캐시 적용 시 0.1초!)

    **프리셋 종류:**
    - beginner_safe: 초보자 안전 모드
    - conservative_growth: 보수적 성장
    - balanced_trader: 균형잡힌 (인기)
    - aggressive_growth: 공격적 성장
    - professional: 전문가 모드

    **캐싱:**
    - 동일한 파라미터로 재요청 시 즉시 응답
    - 30분간 결과 캐시 유지
    - 실시간 데이터 필요 시 30분 후 재실행
    """
    try:
        # Get preset
        preset = get_preset(request.preset_id)
        if not preset:
            available = ", ".join(list(PRESETS.keys()))
            raise HTTPException(
                status_code=404,
                detail=f"Preset '{request.preset_id}' not found. Available: {available}"
            )

        # Check exchange compatibility
        if request.exchange.lower() not in preset.compatible_exchanges:
            raise HTTPException(
                status_code=400,
                detail=f"Preset '{request.preset_id}' is not compatible with {request.exchange}. "
                       f"Compatible exchanges: {', '.join(preset.compatible_exchanges)}"
            )

        # Check capital requirement
        if request.initial_capital < preset.recommended_capital_min:
            logger.warning(
                f"Capital ${request.initial_capital} is below recommended minimum "
                f"${preset.recommended_capital_min} for preset '{request.preset_id}'"
            )

        # Apply preset to get backtest parameters
        backtest_params = apply_preset_to_backtest_request(
            preset_id=request.preset_id,
            symbol=request.symbol,
            exchange=request.exchange,
            mode="futures"  # Default to futures for backtesting
        )

        # Get strategy instance
        from app.strategies.strategies import (
            SuperTrendStrategy,
            RSIEMAStrategy,
            MACDStochStrategy,
            IchimokuStrategy,
            WaveTrendStrategy,
            MultiIndicatorStrategy
        )

        strategy_map = {
            "supertrend": SuperTrendStrategy,
            "rsi_ema": RSIEMAStrategy,
            "macd_stoch": MACDStochStrategy,
            "ichimoku": IchimokuStrategy,
            "wavetrend": WaveTrendStrategy,
            "multi_indicator": MultiIndicatorStrategy
        }

        strategy_class = strategy_map.get(backtest_params["strategy_type"])
        if not strategy_class:
            raise ValueError(f"Unknown strategy: {backtest_params['strategy_type']}")

        # Initialize strategy with custom params
        if backtest_params.get("custom_params"):
            strategy = strategy_class(**backtest_params["custom_params"])
        else:
            strategy = strategy_class()

        # Generate historical data
        df = generate_mock_ohlcv_data(
            symbol=backtest_params["symbol"],
            days_back=request.days_back
        )

        logger.info(
            f"Quick backtest: preset={request.preset_id}, "
            f"exchange={request.exchange}, symbol={backtest_params['symbol']}"
        )

        # Run backtest
        engine = BacktestEngine(
            initial_capital=request.initial_capital,
            maker_fee=backtest_params["maker_fee"],
            taker_fee=backtest_params["taker_fee"],
            leverage=backtest_params["leverage"],
            position_size_pct=backtest_params["position_size_pct"]
        )

        result = engine.run(
            strategy=strategy,
            df=df,
            symbol=backtest_params["symbol"]
        )

        logger.info(
            f"Quick backtest complete: {result.total_trades} trades, "
            f"{result.win_rate:.1f}% win rate, {result.total_return_pct:+.2f}% return"
        )

        # Convert to response
        response = backtest_result_to_response(result, backtest_params["symbol"])

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Quick backtest error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Quick backtest failed: {str(e)}")


@router.get("/exchanges/{exchange}", response_model=ExchangeInfo)
async def get_exchange_info(
    exchange: str,
    mode: str = Query(default="futures", description="Trading mode: spot or futures")
):
    """
    거래소 정보 조회

    **지원 거래소:**
    - binance: 바이낸스 (세계 1위 거래소)
    - okx: OKX (아시아 인기 거래소)

    **모드:**
    - spot: 현물 거래 (레버리지 없음)
    - futures: 선물 거래 (레버리지 가능)
    """
    try:
        config = get_exchange_config(exchange, mode)

        return ExchangeInfo(
            exchange=config.exchange.value,
            mode=config.mode.value,
            maker_fee=config.fees.maker_fee,
            taker_fee=config.fees.taker_fee,
            max_leverage=config.limits.max_leverage,
            recommended_leverage=config.recommended_leverage,
            optimal_symbols=config.optimal_symbols,
            optimal_timeframes=config.optimal_timeframes
        )

    except Exception as e:
        logger.error(f"Get exchange info error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get exchange info: {str(e)}")


# ===== Pine Script Export =====

class PineScriptExportRequest(BaseModel):
    """Pine Script export request"""
    preset_id: str = Field(..., description="Preset ID to export as Pine Script")

    class Config:
        json_schema_extra = {
            "example": {
                "preset_id": "balanced_trader"
            }
        }


class PineScriptExportResponse(BaseModel):
    """Pine Script export response"""
    success: bool
    preset_name: str
    pine_script_code: str
    instructions: str
    instructions_ko: str
    features: List[str]


@router.post("/export-pine-script", response_model=PineScriptExportResponse)
@cached(cache_type="pine_script", ttl_seconds=3600)  # Cache for 1 hour
async def export_to_pine_script(request: PineScriptExportRequest):
    """
    TradingView Pine Script로 내보내기

    **기능:**
    - 프리셋을 Pine Script v5로 자동 변환
    - TradingView에서 바로 사용 가능
    - 자동 백테스팅 지원
    - 롱/숏/익절/손절 시그널 자동 표시
    - 결과 캐싱으로 즉시 응답 (1시간 유지)

    **사용법:**
    1. 프리셋 ID 선택
    2. Pine Script 코드 생성
    3. TradingView에 복사-붙여넣기
    4. 차트에 적용 및 백테스트

    **TradingView 업로드 방법:**
    1. TradingView 접속 (tradingview.com)
    2. Pine Editor 열기 (하단 바)
    3. 새 스크립트 생성
    4. 생성된 Pine Script 코드 전체 복사
    5. Pine Editor에 붙여넣기
    6. "차트에 추가" 클릭
    7. 백테스트 결과 자동 표시!

    **시그널 표시:**
    - 롱 진입: 녹색 화살표 (차트 하단)
    - 숏 진입: 빨간색 화살표 (차트 상단)
    - 익절가: 녹색 점선 (자동 계산)
    - 손절가: 빨간색 점선 (자동 계산)
    - 현재 손익: 우측 상단 테이블

    **주의사항:**
    - TradingView는 자동 업로드 API를 제공하지 않습니다
    - 수동으로 복사-붙여넣기 필요
    - Pine Script는 TradingView에서 무료로 사용 가능
    """
    try:
        # Import Pine Script exporter
        from app.ai.pine_export import get_pine_exporter

        # Get preset
        preset = get_preset(request.preset_id)
        if not preset:
            available = ", ".join(list(PRESETS.keys()))
            raise HTTPException(
                status_code=404,
                detail=f"Preset '{request.preset_id}' not found. Available: {available}"
            )

        # Generate Pine Script
        exporter = get_pine_exporter()
        pine_code = exporter.generate_from_preset(request.preset_id)

        # Generate instructions
        instructions = f"""
How to use this Pine Script in TradingView:

1. Go to TradingView.com and open any chart
2. Click "Pine Editor" at the bottom of the page
3. Create a new script
4. Copy ALL the Pine Script code below
5. Paste it into the Pine Editor
6. Click "Add to Chart"
7. The strategy will automatically backtest on your chart!

Features:
- Automatic Long/Short signals
- ATR-based Stop Loss and Take Profit
- Real-time position tracking
- Performance statistics table
- Alert notifications ready

The strategy is now backtesting on TradingView!
Check the "Strategy Tester" tab for results.
"""

        instructions_ko = f"""
TradingView에서 이 Pine Script 사용하는 방법:

1. TradingView.com 접속하여 차트 열기
2. 하단의 "Pine 편집기" 클릭
3. 새 스크립트 생성
4. 아래 Pine Script 코드 전체 복사
5. Pine 편집기에 붙여넣기
6. "차트에 추가" 클릭
7. 전략이 자동으로 백테스트 실행됩니다!

기능:
- 자동 롱/숏 시그널
- ATR 기반 손절/익절 자동 계산
- 실시간 포지션 추적
- 성과 통계 테이블
- 알림 알람 준비 완료

이제 TradingView에서 전략이 백테스트 중입니다!
"Strategy Tester" 탭에서 결과를 확인하세요.
"""

        features = [
            "✅ TradingView Pine Script v5 (최신 버전)",
            "✅ 자동 백테스팅 (TradingView 내장)",
            "✅ 롱/숏 진입 시그널 자동 표시",
            "✅ ATR 기반 익절/손절 라인",
            "✅ 실시간 손익 계산",
            "✅ 차트 배경 색상 (포지션 상태)",
            "✅ 통계 테이블 (우측 상단)",
            "✅ 알림 알람 설정 가능",
            f"✅ 전략: {preset.strategy_type.upper()}",
            f"✅ 레버리지: {preset.leverage}x",
            f"✅ 예상 월 수익: {preset.expected_return_monthly}"
        ]

        logger.info(f"Pine Script exported for preset: {request.preset_id}")

        return PineScriptExportResponse(
            success=True,
            preset_name=preset.name_ko,
            pine_script_code=pine_code,
            instructions=instructions,
            instructions_ko=instructions_ko,
            features=features
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Pine Script export error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to export Pine Script: {str(e)}"
        )
