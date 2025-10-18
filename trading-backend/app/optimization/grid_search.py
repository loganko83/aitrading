"""
그리드 탐색 (Grid Search) 최적화

Features:
- 전수 조사 방식
- 모든 파라미터 조합 테스트
- 확실한 최적해 보장 (탐색 공간 내)
- 병렬 처리 지원
"""

from typing import Dict, List, Any, Callable, Optional
from itertools import product
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

from .parameter_optimizer import (
    OptimizationConfig,
    OptimizationResult,
    ParameterRange
)

logger = logging.getLogger(__name__)


class GridSearchOptimizer:
    """그리드 탐색 최적화"""

    def __init__(self, config: OptimizationConfig):
        self.config = config
        self.param_ranges = config.parameter_ranges

    def optimize(
        self,
        objective_function: Callable[[Dict[str, Any]], float],
        parallel: bool = False,
        max_workers: int = 4
    ) -> OptimizationResult:
        """
        그리드 탐색 실행

        Args:
            objective_function: 파라미터를 받아 점수를 반환하는 함수
            parallel: 병렬 처리 사용 여부
            max_workers: 병렬 처리 워커 수

        Returns:
            OptimizationResult: 최적화 결과
        """
        # 탐색 공간 생성
        param_names = [pr.name for pr in self.param_ranges]
        param_spaces = [pr.get_search_space() for pr in self.param_ranges]

        # 모든 조합 생성
        all_combinations = list(product(*param_spaces))
        total_combinations = len(all_combinations)

        logger.info(
            f"Grid Search: {total_combinations} combinations, "
            f"parallel={parallel}, workers={max_workers if parallel else 1}"
        )

        start_time = time.time()

        if parallel and total_combinations > 10:
            result = self._parallel_search(
                param_names,
                all_combinations,
                objective_function,
                max_workers
            )
        else:
            result = self._sequential_search(
                param_names,
                all_combinations,
                objective_function
            )

        result.optimization_time_seconds = time.time() - start_time

        logger.info(
            f"Grid Search complete: best_score={result.best_score:.4f}, "
            f"time={result.optimization_time_seconds:.2f}s"
        )

        return result

    def _sequential_search(
        self,
        param_names: List[str],
        all_combinations: List[tuple],
        objective_function: Callable
    ) -> OptimizationResult:
        """순차적 탐색"""
        best_score = float('-inf')
        best_params = {}
        all_results = []

        total = len(all_combinations)

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
                if score > best_score:
                    best_score = score
                    best_params = params.copy()
                    logger.info(
                        f"[{idx + 1}/{total}] New best: score={score:.4f}, params={params}"
                    )

            except Exception as e:
                logger.warning(f"Error evaluating params {params}: {str(e)}")
                continue

            # 진행률 로깅
            if (idx + 1) % max(total // 10, 1) == 0:
                progress = (idx + 1) / total * 100
                logger.info(f"Progress: {progress:.1f}% ({idx + 1}/{total})")

        return OptimizationResult(
            best_parameters=best_params,
            best_score=best_score,
            all_results=all_results,
            total_iterations=len(all_combinations)
        )

    def _parallel_search(
        self,
        param_names: List[str],
        all_combinations: List[tuple],
        objective_function: Callable,
        max_workers: int
    ) -> OptimizationResult:
        """병렬 탐색"""
        best_score = float('-inf')
        best_params = {}
        all_results = []

        total = len(all_combinations)

        def evaluate_params(idx_and_values):
            idx, param_values = idx_and_values
            params = dict(zip(param_names, param_values))

            try:
                score = objective_function(params)
                return {
                    "iteration": idx + 1,
                    "parameters": params,
                    "score": score,
                    "success": True
                }
            except Exception as e:
                logger.warning(f"Error evaluating params {params}: {str(e)}")
                return {
                    "iteration": idx + 1,
                    "parameters": params,
                    "score": float('-inf'),
                    "success": False
                }

        # 병렬 실행
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 작업 제출
            futures = {
                executor.submit(evaluate_params, (idx, combo)): idx
                for idx, combo in enumerate(all_combinations)
            }

            # 결과 수집
            completed = 0
            for future in as_completed(futures):
                result = future.result()
                completed += 1

                if result["success"]:
                    all_results.append({
                        "iteration": result["iteration"],
                        "parameters": result["parameters"],
                        "score": result["score"]
                    })

                    # 최고 점수 갱신
                    if result["score"] > best_score:
                        best_score = result["score"]
                        best_params = result["parameters"].copy()
                        logger.info(
                            f"[{completed}/{total}] New best: "
                            f"score={best_score:.4f}, params={best_params}"
                        )

                # 진행률 로깅
                if completed % max(total // 10, 1) == 0:
                    progress = completed / total * 100
                    logger.info(f"Progress: {progress:.1f}% ({completed}/{total})")

        return OptimizationResult(
            best_parameters=best_params,
            best_score=best_score,
            all_results=all_results,
            total_iterations=len(all_combinations)
        )


def smart_grid_search(
    config: OptimizationConfig,
    objective_function: Callable[[Dict[str, Any]], float],
    coarse_to_fine: bool = True
) -> OptimizationResult:
    """
    스마트 그리드 탐색 (Coarse-to-Fine)

    전략:
    1. 먼저 큰 간격으로 빠르게 탐색 (Coarse)
    2. 최고 영역 주변을 세밀하게 탐색 (Fine)

    장점:
    - 계산량 대폭 감소 (90% 이상)
    - 거의 동일한 최적해 발견
    """
    if not coarse_to_fine:
        # 일반 그리드 탐색
        optimizer = GridSearchOptimizer(config)
        return optimizer.optimize(objective_function)

    logger.info("Smart Grid Search: Coarse-to-Fine strategy")

    # Phase 1: Coarse search (큰 간격)
    coarse_ranges = []
    for param_range in config.parameter_ranges:
        if param_range.param_type == "int":
            step = max(param_range.step or 1, 5)  # 간격을 크게
            coarse_ranges.append(
                ParameterRange(
                    name=param_range.name,
                    min_value=param_range.min_value,
                    max_value=param_range.max_value,
                    step=step,
                    param_type=param_range.param_type
                )
            )
        else:
            # float: 5개 지점만 샘플링
            coarse_ranges.append(
                ParameterRange(
                    name=param_range.name,
                    min_value=param_range.min_value,
                    max_value=param_range.max_value,
                    values=list(
                        np.linspace(param_range.min_value, param_range.max_value, 5)
                    ),
                    param_type=param_range.param_type
                )
            )

    coarse_config = OptimizationConfig(
        method=config.method,
        objective=config.objective,
        parameter_ranges=coarse_ranges
    )

    coarse_optimizer = GridSearchOptimizer(coarse_config)
    coarse_result = coarse_optimizer.optimize(objective_function)

    logger.info(
        f"Coarse search complete: best_score={coarse_result.best_score:.4f}, "
        f"iterations={coarse_result.total_iterations}"
    )

    # Phase 2: Fine search (최고 영역 주변)
    fine_ranges = []
    for param_range in config.parameter_ranges:
        best_value = coarse_result.best_parameters[param_range.name]

        if param_range.param_type == "int":
            # ±5 범위
            fine_min = max(param_range.min_value, best_value - 5)
            fine_max = min(param_range.max_value, best_value + 5)
            fine_ranges.append(
                ParameterRange(
                    name=param_range.name,
                    min_value=fine_min,
                    max_value=fine_max,
                    step=1,
                    param_type=param_range.param_type
                )
            )
        else:
            # ±20% 범위
            range_size = param_range.max_value - param_range.min_value
            fine_min = max(param_range.min_value, best_value - range_size * 0.2)
            fine_max = min(param_range.max_value, best_value + range_size * 0.2)
            fine_ranges.append(
                ParameterRange(
                    name=param_range.name,
                    min_value=fine_min,
                    max_value=fine_max,
                    values=list(np.linspace(fine_min, fine_max, 10)),
                    param_type=param_range.param_type
                )
            )

    fine_config = OptimizationConfig(
        method=config.method,
        objective=config.objective,
        parameter_ranges=fine_ranges
    )

    fine_optimizer = GridSearchOptimizer(fine_config)
    fine_result = fine_optimizer.optimize(objective_function)

    logger.info(
        f"Fine search complete: best_score={fine_result.best_score:.4f}, "
        f"iterations={fine_result.total_iterations}"
    )

    # 두 결과 중 최고 선택
    if fine_result.best_score > coarse_result.best_score:
        final_result = fine_result
    else:
        final_result = coarse_result

    # 전체 결과 병합
    final_result.all_results = coarse_result.all_results + fine_result.all_results
    final_result.total_iterations = (
        coarse_result.total_iterations + fine_result.total_iterations
    )

    logger.info(
        f"Smart Grid Search complete: best_score={final_result.best_score:.4f}, "
        f"total_iterations={final_result.total_iterations}"
    )

    return final_result


# numpy import for smart_grid_search
import numpy as np
