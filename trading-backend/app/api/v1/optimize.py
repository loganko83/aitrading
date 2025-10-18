"""
파라미터 최적화 API

Features:
- Grid Search 최적화
- Genetic Algorithm 최적화
- Walk-Forward 검증
- 과적합 탐지
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

from app.optimization.parameter_optimizer import (
    ParameterOptimizer,
    OptimizationConfig,
    OptimizationMethod,
    ObjectiveType,
    ParameterRange,
    create_default_ranges
)
from app.optimization.genetic_optimizer import adaptive_genetic_optimizer
from app.optimization.grid_search import smart_grid_search
from app.backtesting.engine import BacktestEngine
from app.api.v1.backtest import generate_mock_ohlcv_data
from app.strategies.strategies import (
    SuperTrendStrategy,
    RSIEMAStrategy,
    MACDStochStrategy
)

router = APIRouter()
logger = logging.getLogger(__name__)


# ===== Request/Response Models =====

class ParameterRangeModel(BaseModel):
    """파라미터 범위"""
    name: str = Field(..., description="파라미터 이름")
    min_value: float = Field(..., description="최소값")
    max_value: float = Field(..., description="최대값")
    step: Optional[float] = Field(None, description="증가 간격")
    param_type: str = Field(default="float", description="파라미터 타입: int, float")


class OptimizationRequest(BaseModel):
    """최적화 요청"""
    strategy_type: str = Field(..., description="전략 타입: supertrend, rsi_ema, macd_stoch")
    method: str = Field(
        default="grid_search",
        description="최적화 방법: grid_search, genetic, random_search"
    )
    objective: str = Field(
        default="maximize_sharpe",
        description="목표: maximize_return, maximize_sharpe, minimize_drawdown, maximize_win_rate"
    )

    # 데이터 설정
    symbol: str = Field(default="BTCUSDT", description="트레이딩 심볼")
    days_back: int = Field(default=90, ge=30, le=365, description="백테스트 기간 (일)")
    initial_capital: float = Field(default=10000, ge=1000, description="초기 자본")

    # 파라미터 범위 (선택사항, 없으면 기본값 사용)
    parameter_ranges: Optional[List[ParameterRangeModel]] = None

    # 최적화 설정
    max_iterations: int = Field(default=100, ge=10, le=500, description="최대 반복 횟수")
    enable_walk_forward: bool = Field(default=True, description="Walk-Forward 검증 사용")

    # 유전 알고리즘 설정 (method=genetic일 때)
    population_size: Optional[int] = Field(50, ge=10, le=200, description="개체 수")
    mutation_rate: Optional[float] = Field(0.1, ge=0.01, le=0.5, description="돌연변이율")

    class Config:
        json_schema_extra = {
            "example": {
                "strategy_type": "supertrend",
                "method": "grid_search",
                "objective": "maximize_sharpe",
                "symbol": "BTCUSDT",
                "days_back": 90,
                "initial_capital": 10000,
                "max_iterations": 50
            }
        }


class OptimizationResponse(BaseModel):
    """최적화 결과"""
    success: bool
    best_parameters: Dict[str, Any]
    best_score: float
    objective_type: str

    # 검증 결과
    train_score: Optional[float] = None
    validation_score: Optional[float] = None
    robustness_score: Optional[float] = None
    is_overfit: bool = False

    # 통계
    total_iterations: int
    optimization_time_seconds: float
    optimization_method: str

    # 상위 결과 (Top 5)
    top_results: List[Dict[str, Any]] = []

    # 추천사항
    recommendations: List[str] = []

    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class OptimizationStatusResponse(BaseModel):
    """최적화 진행 상태"""
    status: str  # pending, running, completed, failed
    progress_pct: float = 0.0
    current_iteration: int = 0
    total_iterations: int = 0
    best_score_so_far: Optional[float] = None
    estimated_time_remaining_seconds: Optional[float] = None


# ===== API Endpoints =====

@router.post("/optimize", response_model=OptimizationResponse)
async def run_optimization(request: OptimizationRequest):
    """
    전략 파라미터 자동 최적화

    **기능:**
    - 최적 파라미터 자동 탐색
    - Walk-Forward 검증으로 과적합 방지
    - 여러 최적화 알고리즘 지원

    **최적화 방법:**
    - **grid_search**: 그리드 탐색 (전수조사, 확실하지만 느림)
    - **genetic**: 유전 알고리즘 (빠르고 효율적)
    - **random_search**: 랜덤 탐색 (빠른 테스트용)

    **목표 함수:**
    - **maximize_return**: 수익률 최대화
    - **maximize_sharpe**: 샤프 비율 최대화 (권장)
    - **minimize_drawdown**: 낙폭 최소화
    - **maximize_win_rate**: 승률 최대화

    **주의사항:**
    - Grid Search는 파라미터가 많을수록 오래 걸림
    - 과적합 위험이 있으므로 Walk-Forward 검증 필수
    - 최소 90일 이상 데이터 사용 권장
    """
    try:
        logger.info(
            f"Optimization request: strategy={request.strategy_type}, "
            f"method={request.method}, objective={request.objective}"
        )

        # 파라미터 범위 설정
        if request.parameter_ranges:
            param_ranges = [
                ParameterRange(
                    name=pr.name,
                    min_value=pr.min_value,
                    max_value=pr.max_value,
                    step=pr.step,
                    param_type=pr.param_type
                )
                for pr in request.parameter_ranges
            ]
        else:
            # 기본 범위 사용
            param_ranges = create_default_ranges(request.strategy_type)

        # 최적화 설정
        config = OptimizationConfig(
            method=OptimizationMethod(request.method),
            objective=ObjectiveType(request.objective),
            parameter_ranges=param_ranges,
            max_iterations=request.max_iterations,
            enable_walk_forward=request.enable_walk_forward,
            population_size=request.population_size or 50,
            mutation_rate=request.mutation_rate or 0.1
        )

        # 백테스트 데이터 생성
        df = generate_mock_ohlcv_data(
            symbol=request.symbol,
            days_back=request.days_back
        )

        # 목적 함수 정의
        def objective_function(params: Dict[str, Any]) -> float:
            """파라미터를 받아 백테스트 점수 반환"""
            try:
                # 전략 인스턴스 생성
                if request.strategy_type == "supertrend":
                    strategy = SuperTrendStrategy(**params)
                elif request.strategy_type == "rsi_ema":
                    strategy = RSIEMAStrategy(**params)
                elif request.strategy_type == "macd_stoch":
                    strategy = MACDStochStrategy(**params)
                else:
                    raise ValueError(f"Unknown strategy: {request.strategy_type}")

                # 백테스트 실행
                engine = BacktestEngine(
                    initial_capital=request.initial_capital,
                    maker_fee=0.0002,
                    taker_fee=0.0004
                )

                result = engine.run(strategy=strategy, df=df, symbol=request.symbol)

                # 목표 함수에 따라 점수 계산
                if config.objective == ObjectiveType.MAXIMIZE_RETURN:
                    return result.total_return_pct
                elif config.objective == ObjectiveType.MAXIMIZE_SHARPE:
                    return result.sharpe_ratio
                elif config.objective == ObjectiveType.MINIMIZE_DRAWDOWN:
                    return -result.max_drawdown_pct  # 음수로 변환
                elif config.objective == ObjectiveType.MAXIMIZE_WIN_RATE:
                    return result.win_rate
                else:
                    return result.total_return_pct

            except Exception as e:
                logger.warning(f"Error in objective function with params {params}: {str(e)}")
                return float('-inf')  # 실패한 파라미터는 최하 점수

        # 최적화 실행
        optimizer = ParameterOptimizer(config)
        optimization_result = optimizer.optimize(objective_function)

        # 과적합 검사
        is_overfit = optimization_result.is_overfit()
        robustness_score = optimization_result.get_robustness_score()

        # 상위 결과 추출 (Top 5)
        sorted_results = sorted(
            optimization_result.all_results,
            key=lambda x: x.get("score", float('-inf')),
            reverse=True
        )
        top_results = sorted_results[:5]

        # 추천사항 생성
        recommendations = []

        if is_overfit:
            recommendations.append(
                "⚠️ 과적합 의심: 검증 점수가 학습 점수보다 낮습니다. "
                "더 긴 기간 데이터로 재검증하세요."
            )

        if robustness_score < 50:
            recommendations.append(
                "⚠️ 낮은 견고성: Walk-Forward 점수가 불안정합니다. "
                "더 안정적인 파라미터를 찾아보세요."
            )
        elif robustness_score > 80:
            recommendations.append(
                "✅ 높은 견고성: 파라미터가 안정적으로 작동합니다."
            )

        if optimization_result.total_iterations < 50 and request.method == "grid_search":
            recommendations.append(
                "💡 더 많은 반복 횟수를 시도하면 더 나은 결과를 얻을 수 있습니다."
            )

        if len(param_ranges) > 3 and request.method == "grid_search":
            recommendations.append(
                "💡 파라미터가 많습니다. Genetic Algorithm을 사용하면 더 빠릅니다."
            )

        logger.info(
            f"Optimization complete: best_score={optimization_result.best_score:.4f}, "
            f"iterations={optimization_result.total_iterations}, "
            f"time={optimization_result.optimization_time_seconds:.2f}s"
        )

        return OptimizationResponse(
            success=True,
            best_parameters=optimization_result.best_parameters,
            best_score=optimization_result.best_score,
            objective_type=request.objective,
            train_score=optimization_result.train_score,
            validation_score=optimization_result.validation_score,
            robustness_score=robustness_score,
            is_overfit=is_overfit,
            total_iterations=optimization_result.total_iterations,
            optimization_time_seconds=optimization_result.optimization_time_seconds,
            optimization_method=request.method,
            top_results=top_results,
            recommendations=recommendations
        )

    except Exception as e:
        logger.error(f"Optimization error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"최적화 실패: {str(e)}"
        )


@router.get("/optimize/presets")
async def get_optimization_presets():
    """
    최적화 프리셋 조회

    Returns:
        - 전략별 추천 파라미터 범위
        - 최적화 방법 가이드
        - 목표 함수 설명
    """
    return {
        "strategies": {
            "supertrend": {
                "description": "SuperTrend 전략 (추세 추종)",
                "default_ranges": [
                    {"name": "period", "min": 5, "max": 20, "step": 1, "type": "int"},
                    {"name": "multiplier", "min": 1.0, "max": 5.0, "step": 0.5, "type": "float"}
                ],
                "recommended_method": "grid_search",
                "recommended_objective": "maximize_sharpe"
            },
            "rsi_ema": {
                "description": "RSI + EMA 크로스오버",
                "default_ranges": [
                    {"name": "rsi_period", "min": 7, "max": 21, "step": 1, "type": "int"},
                    {"name": "rsi_overbought", "min": 65, "max": 80, "step": 5, "type": "int"},
                    {"name": "rsi_oversold", "min": 20, "max": 35, "step": 5, "type": "int"},
                    {"name": "ema_fast", "min": 5, "max": 20, "step": 5, "type": "int"},
                    {"name": "ema_slow", "min": 20, "max": 50, "step": 10, "type": "int"}
                ],
                "recommended_method": "genetic",
                "recommended_objective": "maximize_sharpe"
            },
            "macd_stoch": {
                "description": "MACD + Stochastic RSI",
                "default_ranges": [
                    {"name": "macd_fast", "min": 8, "max": 16, "step": 2, "type": "int"},
                    {"name": "macd_slow", "min": 20, "max": 30, "step": 2, "type": "int"},
                    {"name": "macd_signal", "min": 7, "max": 12, "step": 1, "type": "int"}
                ],
                "recommended_method": "genetic",
                "recommended_objective": "maximize_return"
            }
        },
        "optimization_methods": {
            "grid_search": {
                "description": "그리드 탐색 (전수조사)",
                "pros": ["확실한 최적해", "간단함"],
                "cons": ["느림", "파라미터 많으면 비실용적"],
                "recommended_for": "파라미터 2-3개 이하, 정확도 중시"
            },
            "genetic": {
                "description": "유전 알고리즘",
                "pros": ["빠름", "다수 파라미터 처리 가능", "효율적"],
                "cons": ["국소 최적해 가능성"],
                "recommended_for": "파라미터 4개 이상, 속도 중시"
            },
            "random_search": {
                "description": "랜덤 탐색",
                "pros": ["매우 빠름", "간단함"],
                "cons": ["정확도 낮음"],
                "recommended_for": "빠른 테스트, 대략적 범위 파악"
            }
        },
        "objectives": {
            "maximize_return": {
                "description": "수익률 최대화",
                "metric": "총 수익률 (%)",
                "recommended_for": "수익 중시"
            },
            "maximize_sharpe": {
                "description": "샤프 비율 최대화",
                "metric": "샤프 비율",
                "recommended_for": "리스크 대비 수익 균형 (권장)"
            },
            "minimize_drawdown": {
                "description": "낙폭 최소화",
                "metric": "최대 낙폭 (%)",
                "recommended_for": "안정성 중시"
            },
            "maximize_win_rate": {
                "description": "승률 최대화",
                "metric": "승률 (%)",
                "recommended_for": "높은 승률 선호"
            }
        }
    }
