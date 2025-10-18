"""
자동 파라미터 최적화 엔진

Features:
- 최적 파라미터 자동 탐색
- 다양한 최적화 알고리즘 지원
- 과적합 방지 (Walk-Forward)
- 파라미터 제약 조건
"""

from typing import Dict, List, Any, Tuple, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
import pandas as pd
import numpy as np
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class OptimizationMethod(str, Enum):
    """최적화 방법"""
    GRID_SEARCH = "grid_search"  # 그리드 탐색 (전수조사)
    GENETIC = "genetic"  # 유전 알고리즘
    RANDOM_SEARCH = "random_search"  # 랜덤 탐색
    BAYESIAN = "bayesian"  # 베이지안 최적화


class ObjectiveType(str, Enum):
    """최적화 목표"""
    MAXIMIZE_RETURN = "maximize_return"  # 수익률 최대화
    MAXIMIZE_SHARPE = "maximize_sharpe"  # 샤프 비율 최대화
    MINIMIZE_DRAWDOWN = "minimize_drawdown"  # 낙폭 최소화
    MAXIMIZE_WIN_RATE = "maximize_win_rate"  # 승률 최대화
    CUSTOM = "custom"  # 사용자 정의


@dataclass
class ParameterRange:
    """파라미터 범위 정의"""
    name: str
    min_value: float
    max_value: float
    step: Optional[float] = None
    values: Optional[List[Any]] = None  # 이산값 (예: [10, 20, 30])
    param_type: str = "float"  # float, int, bool, str

    def get_search_space(self) -> List[Any]:
        """탐색 공간 생성"""
        if self.values is not None:
            return self.values

        if self.param_type == "int":
            step = self.step or 1
            return list(range(int(self.min_value), int(self.max_value) + 1, int(step)))
        elif self.param_type == "float":
            if self.step is None:
                # 기본: 10개 균등 분할
                return list(np.linspace(self.min_value, self.max_value, 10))
            else:
                return list(np.arange(self.min_value, self.max_value + self.step, self.step))
        else:
            raise ValueError(f"Unsupported param_type: {self.param_type}")

    def clip_value(self, value: Any) -> Any:
        """값을 범위 내로 제한"""
        if self.param_type in ["int", "float"]:
            return max(self.min_value, min(self.max_value, value))
        return value


@dataclass
class OptimizationConfig:
    """최적화 설정"""
    method: OptimizationMethod
    objective: ObjectiveType
    parameter_ranges: List[ParameterRange]

    # 최적화 제약
    max_iterations: int = 100
    convergence_threshold: float = 0.001
    early_stopping_patience: int = 10

    # Walk-Forward 검증
    enable_walk_forward: bool = True
    train_period_pct: float = 0.7  # 70% 학습, 30% 검증
    walk_forward_windows: int = 3

    # 과적합 방지
    min_trades_required: int = 30
    max_correlation_threshold: float = 0.8

    # 유전 알고리즘 설정 (method=genetic일 때)
    population_size: int = 50
    mutation_rate: float = 0.1
    crossover_rate: float = 0.7
    elite_size: int = 5


@dataclass
class OptimizationResult:
    """최적화 결과"""
    best_parameters: Dict[str, Any]
    best_score: float
    all_results: List[Dict[str, Any]] = field(default_factory=list)

    # 검증 결과
    train_score: Optional[float] = None
    validation_score: Optional[float] = None
    walk_forward_scores: List[float] = field(default_factory=list)

    # 통계
    total_iterations: int = 0
    convergence_iteration: Optional[int] = None
    optimization_time_seconds: float = 0.0

    # 메타데이터
    optimization_method: str = ""
    objective_type: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def get_robustness_score(self) -> float:
        """견고성 점수 (0-100)"""
        if not self.walk_forward_scores or self.train_score is None:
            return 0.0

        # 학습-검증 일관성
        if self.validation_score is not None:
            consistency = 1 - abs(self.train_score - self.validation_score) / max(self.train_score, 0.01)
        else:
            consistency = 0.5

        # Walk-Forward 안정성
        if len(self.walk_forward_scores) > 1:
            std_score = np.std(self.walk_forward_scores)
            mean_score = np.mean(self.walk_forward_scores)
            stability = 1 - (std_score / max(mean_score, 0.01))
        else:
            stability = 0.5

        return (consistency + stability) / 2 * 100

    def is_overfit(self) -> bool:
        """과적합 여부 판단"""
        if self.validation_score is None or self.train_score is None:
            return False

        # 검증 점수가 학습 점수보다 20% 이상 낮으면 과적합 의심
        if self.validation_score < self.train_score * 0.8:
            return True

        # Walk-Forward 점수가 너무 분산되어 있으면 과적합
        if len(self.walk_forward_scores) > 1:
            std_score = np.std(self.walk_forward_scores)
            mean_score = np.mean(self.walk_forward_scores)
            if std_score > mean_score * 0.5:
                return True

        return False


class ParameterOptimizer:
    """파라미터 최적화 엔진"""

    def __init__(self, config: OptimizationConfig):
        self.config = config
        self.best_score = float('-inf') if self._is_maximization() else float('inf')
        self.best_params = {}
        self.iteration_count = 0
        self.no_improvement_count = 0
        self.all_results = []

    def _is_maximization(self) -> bool:
        """최대화 문제인지 확인"""
        return self.config.objective in [
            ObjectiveType.MAXIMIZE_RETURN,
            ObjectiveType.MAXIMIZE_SHARPE,
            ObjectiveType.MAXIMIZE_WIN_RATE
        ]

    def _is_better(self, new_score: float, current_best: float) -> bool:
        """새 점수가 더 좋은지 확인"""
        if self._is_maximization():
            return new_score > current_best
        else:
            return new_score < current_best

    def _calculate_objective(
        self,
        backtest_result: Any,
        objective_type: ObjectiveType
    ) -> float:
        """목적 함수 계산"""
        if objective_type == ObjectiveType.MAXIMIZE_RETURN:
            return backtest_result.total_return_pct

        elif objective_type == ObjectiveType.MAXIMIZE_SHARPE:
            return backtest_result.sharpe_ratio

        elif objective_type == ObjectiveType.MINIMIZE_DRAWDOWN:
            return -backtest_result.max_drawdown_pct  # 음수로 변환 (최소화 → 최대화)

        elif objective_type == ObjectiveType.MAXIMIZE_WIN_RATE:
            return backtest_result.win_rate

        else:
            # 기본: 수익률
            return backtest_result.total_return_pct

    def optimize(
        self,
        objective_function: Callable[[Dict[str, Any]], float],
        initial_params: Optional[Dict[str, Any]] = None
    ) -> OptimizationResult:
        """
        파라미터 최적화 실행

        Args:
            objective_function: 파라미터를 받아 점수를 반환하는 함수
            initial_params: 초기 파라미터 (선택사항)

        Returns:
            OptimizationResult: 최적화 결과
        """
        import time
        start_time = time.time()

        logger.info(f"Starting optimization: method={self.config.method.value}")

        if self.config.method == OptimizationMethod.GRID_SEARCH:
            result = self._grid_search(objective_function)

        elif self.config.method == OptimizationMethod.GENETIC:
            result = self._genetic_algorithm(objective_function, initial_params)

        elif self.config.method == OptimizationMethod.RANDOM_SEARCH:
            result = self._random_search(objective_function)

        else:
            raise ValueError(f"Unsupported optimization method: {self.config.method}")

        # 메타데이터 추가
        result.optimization_time_seconds = time.time() - start_time
        result.optimization_method = self.config.method.value
        result.objective_type = self.config.objective.value

        logger.info(
            f"Optimization complete: best_score={result.best_score:.4f}, "
            f"iterations={result.total_iterations}, time={result.optimization_time_seconds:.2f}s"
        )

        return result

    def _grid_search(self, objective_function: Callable) -> OptimizationResult:
        """그리드 탐색 최적화"""
        from itertools import product

        # 탐색 공간 생성
        param_names = [pr.name for pr in self.config.parameter_ranges]
        param_spaces = [pr.get_search_space() for pr in self.config.parameter_ranges]

        # 모든 조합 생성
        all_combinations = list(product(*param_spaces))
        total_combinations = len(all_combinations)

        logger.info(f"Grid search: {total_combinations} combinations to evaluate")

        best_score = float('-inf') if self._is_maximization() else float('inf')
        best_params = {}
        all_results = []

        for idx, param_values in enumerate(all_combinations):
            # 파라미터 딕셔너리 생성
            params = dict(zip(param_names, param_values))

            # 점수 계산
            try:
                score = objective_function(params)

                result_entry = {
                    "iteration": idx + 1,
                    "parameters": params.copy(),
                    "score": score
                }
                all_results.append(result_entry)

                # 최고 점수 갱신
                if self._is_better(score, best_score):
                    best_score = score
                    best_params = params.copy()
                    logger.info(f"New best: score={score:.4f}, params={params}")

            except Exception as e:
                logger.warning(f"Error evaluating params {params}: {str(e)}")
                continue

            # 진행률 로깅
            if (idx + 1) % max(total_combinations // 10, 1) == 0:
                progress = (idx + 1) / total_combinations * 100
                logger.info(f"Progress: {progress:.1f}% ({idx + 1}/{total_combinations})")

        return OptimizationResult(
            best_parameters=best_params,
            best_score=best_score,
            all_results=all_results,
            total_iterations=len(all_combinations)
        )

    def _random_search(self, objective_function: Callable) -> OptimizationResult:
        """랜덤 탐색 최적화"""
        import random

        logger.info(f"Random search: {self.config.max_iterations} iterations")

        best_score = float('-inf') if self._is_maximization() else float('inf')
        best_params = {}
        all_results = []

        for iteration in range(self.config.max_iterations):
            # 랜덤 파라미터 생성
            params = {}
            for param_range in self.config.parameter_ranges:
                search_space = param_range.get_search_space()
                params[param_range.name] = random.choice(search_space)

            # 점수 계산
            try:
                score = objective_function(params)

                result_entry = {
                    "iteration": iteration + 1,
                    "parameters": params.copy(),
                    "score": score
                }
                all_results.append(result_entry)

                # 최고 점수 갱신
                if self._is_better(score, best_score):
                    improvement = abs(score - best_score)
                    best_score = score
                    best_params = params.copy()
                    self.no_improvement_count = 0
                    logger.info(f"New best: score={score:.4f}, params={params}")
                else:
                    self.no_improvement_count += 1

                # Early stopping
                if self.no_improvement_count >= self.config.early_stopping_patience:
                    logger.info(f"Early stopping at iteration {iteration + 1}")
                    break

            except Exception as e:
                logger.warning(f"Error evaluating params {params}: {str(e)}")
                continue

        return OptimizationResult(
            best_parameters=best_params,
            best_score=best_score,
            all_results=all_results,
            total_iterations=iteration + 1
        )

    def _genetic_algorithm(
        self,
        objective_function: Callable,
        initial_params: Optional[Dict[str, Any]] = None
    ) -> OptimizationResult:
        """유전 알고리즘 최적화 (기본 구현)"""
        # 유전 알고리즘은 genetic_optimizer.py에서 완전히 구현
        # 여기서는 간단한 래퍼만 제공
        from .genetic_optimizer import GeneticOptimizer

        ga_optimizer = GeneticOptimizer(self.config)
        return ga_optimizer.optimize(objective_function, initial_params)


def create_default_ranges(strategy_type: str) -> List[ParameterRange]:
    """전략별 기본 파라미터 범위"""
    if strategy_type == "supertrend":
        return [
            ParameterRange(name="period", min_value=5, max_value=20, step=1, param_type="int"),
            ParameterRange(name="multiplier", min_value=1.0, max_value=5.0, step=0.5, param_type="float")
        ]

    elif strategy_type == "rsi_ema":
        return [
            ParameterRange(name="rsi_period", min_value=7, max_value=21, step=1, param_type="int"),
            ParameterRange(name="rsi_overbought", min_value=65, max_value=80, step=5, param_type="int"),
            ParameterRange(name="rsi_oversold", min_value=20, max_value=35, step=5, param_type="int"),
            ParameterRange(name="ema_fast", min_value=5, max_value=20, step=5, param_type="int"),
            ParameterRange(name="ema_slow", min_value=20, max_value=50, step=10, param_type="int")
        ]

    elif strategy_type == "macd_stoch":
        return [
            ParameterRange(name="macd_fast", min_value=8, max_value=16, step=2, param_type="int"),
            ParameterRange(name="macd_slow", min_value=20, max_value=30, step=2, param_type="int"),
            ParameterRange(name="macd_signal", min_value=7, max_value=12, step=1, param_type="int"),
            ParameterRange(name="stoch_k", min_value=10, max_value=20, step=2, param_type="int"),
            ParameterRange(name="stoch_d", min_value=3, max_value=7, step=1, param_type="int")
        ]

    else:
        # 기본 범위
        return [
            ParameterRange(name="period", min_value=10, max_value=30, step=5, param_type="int")
        ]
