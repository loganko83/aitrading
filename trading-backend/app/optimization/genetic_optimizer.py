"""
유전 알고리즘 기반 파라미터 최적화

Features:
- Population-based 탐색
- Crossover (교배)
- Mutation (돌연변이)
- Elite preservation (엘리트 보존)
"""

from typing import Dict, List, Any, Callable, Optional, Tuple
import random
import numpy as np
import logging

from .parameter_optimizer import (
    OptimizationConfig,
    OptimizationResult,
    ParameterRange
)

logger = logging.getLogger(__name__)


class Individual:
    """개체 (파라미터 조합)"""

    def __init__(self, genes: Dict[str, Any], fitness: Optional[float] = None):
        self.genes = genes  # 파라미터
        self.fitness = fitness  # 적합도 (점수)

    def __repr__(self):
        return f"Individual(fitness={self.fitness}, genes={self.genes})"


class GeneticOptimizer:
    """유전 알고리즘 최적화"""

    def __init__(self, config: OptimizationConfig):
        self.config = config
        self.param_ranges = {pr.name: pr for pr in config.parameter_ranges}
        self.population: List[Individual] = []
        self.generation = 0

    def optimize(
        self,
        objective_function: Callable[[Dict[str, Any]], float],
        initial_params: Optional[Dict[str, Any]] = None
    ) -> OptimizationResult:
        """
        유전 알고리즘 실행

        Args:
            objective_function: 파라미터를 받아 점수를 반환하는 함수
            initial_params: 초기 파라미터 (선택사항)

        Returns:
            OptimizationResult: 최적화 결과
        """
        logger.info(
            f"Genetic Algorithm: population={self.config.population_size}, "
            f"max_generations={self.config.max_iterations}"
        )

        # 초기 집단 생성
        self._initialize_population(initial_params)

        # 적합도 평가
        self._evaluate_population(objective_function)

        best_individual = max(self.population, key=lambda x: x.fitness)
        best_score = best_individual.fitness
        best_params = best_individual.genes.copy()

        all_results = []
        no_improvement_count = 0

        # 세대 진화
        for generation in range(self.config.max_iterations):
            self.generation = generation + 1

            # 선택, 교배, 돌연변이
            new_population = self._evolve_population()

            # 적합도 평가
            self.population = new_population
            self._evaluate_population(objective_function)

            # 최고 개체 추적
            current_best = max(self.population, key=lambda x: x.fitness)

            # 결과 기록
            all_results.append({
                "iteration": generation + 1,
                "parameters": current_best.genes.copy(),
                "score": current_best.fitness,
                "avg_fitness": np.mean([ind.fitness for ind in self.population])
            })

            # 개선 체크
            if current_best.fitness > best_score:
                improvement = current_best.fitness - best_score
                best_score = current_best.fitness
                best_params = current_best.genes.copy()
                no_improvement_count = 0

                logger.info(
                    f"Gen {generation + 1}: New best fitness={best_score:.4f} "
                    f"(+{improvement:.4f}), params={best_params}"
                )
            else:
                no_improvement_count += 1

            # Early stopping
            if no_improvement_count >= self.config.early_stopping_patience:
                logger.info(f"Early stopping at generation {generation + 1}")
                break

            # 진행률 로깅
            if (generation + 1) % 10 == 0:
                avg_fitness = np.mean([ind.fitness for ind in self.population])
                logger.info(
                    f"Gen {generation + 1}: Best={best_score:.4f}, "
                    f"Avg={avg_fitness:.4f}"
                )

        return OptimizationResult(
            best_parameters=best_params,
            best_score=best_score,
            all_results=all_results,
            total_iterations=generation + 1
        )

    def _initialize_population(self, initial_params: Optional[Dict[str, Any]] = None):
        """초기 집단 생성"""
        self.population = []

        # 초기 파라미터가 주어지면 첫 개체로 사용
        if initial_params:
            self.population.append(Individual(genes=initial_params.copy()))

        # 나머지 랜덤 생성
        while len(self.population) < self.config.population_size:
            genes = {}
            for param_name, param_range in self.param_ranges.items():
                search_space = param_range.get_search_space()
                genes[param_name] = random.choice(search_space)

            self.population.append(Individual(genes=genes))

        logger.info(f"Initialized population with {len(self.population)} individuals")

    def _evaluate_population(self, objective_function: Callable):
        """집단 적합도 평가"""
        for individual in self.population:
            if individual.fitness is None:
                try:
                    individual.fitness = objective_function(individual.genes)
                except Exception as e:
                    logger.warning(f"Error evaluating individual {individual.genes}: {str(e)}")
                    individual.fitness = float('-inf')  # 실패한 개체는 최하 점수

    def _evolve_population(self) -> List[Individual]:
        """세대 진화 (선택, 교배, 돌연변이)"""
        new_population = []

        # 1. 엘리트 보존 (상위 N개 그대로 유지)
        sorted_pop = sorted(self.population, key=lambda x: x.fitness, reverse=True)
        elite_individuals = sorted_pop[:self.config.elite_size]
        new_population.extend(elite_individuals)

        # 2. 교배 및 돌연변이로 나머지 채우기
        while len(new_population) < self.config.population_size:
            # 부모 선택 (토너먼트 선택)
            parent1 = self._tournament_selection()
            parent2 = self._tournament_selection()

            # 교배
            if random.random() < self.config.crossover_rate:
                child1, child2 = self._crossover(parent1, parent2)
            else:
                child1, child2 = parent1, parent2

            # 돌연변이
            if random.random() < self.config.mutation_rate:
                child1 = self._mutate(child1)
            if random.random() < self.config.mutation_rate:
                child2 = self._mutate(child2)

            # 새 세대에 추가
            new_population.append(Individual(genes=child1.genes.copy()))
            if len(new_population) < self.config.population_size:
                new_population.append(Individual(genes=child2.genes.copy()))

        return new_population[:self.config.population_size]

    def _tournament_selection(self, tournament_size: int = 3) -> Individual:
        """토너먼트 선택 (상위 K개 중 최고 선택)"""
        tournament = random.sample(self.population, min(tournament_size, len(self.population)))
        return max(tournament, key=lambda x: x.fitness)

    def _crossover(self, parent1: Individual, parent2: Individual) -> Tuple[Individual, Individual]:
        """교배 (Uniform Crossover)"""
        child1_genes = {}
        child2_genes = {}

        for param_name in self.param_ranges.keys():
            if random.random() < 0.5:
                child1_genes[param_name] = parent1.genes[param_name]
                child2_genes[param_name] = parent2.genes[param_name]
            else:
                child1_genes[param_name] = parent2.genes[param_name]
                child2_genes[param_name] = parent1.genes[param_name]

        return Individual(genes=child1_genes), Individual(genes=child2_genes)

    def _mutate(self, individual: Individual) -> Individual:
        """돌연변이 (랜덤 파라미터 변경)"""
        mutated_genes = individual.genes.copy()

        # 하나의 파라미터만 변경
        param_to_mutate = random.choice(list(self.param_ranges.keys()))
        param_range = self.param_ranges[param_to_mutate]

        # 새 값 랜덤 선택
        search_space = param_range.get_search_space()
        mutated_genes[param_to_mutate] = random.choice(search_space)

        return Individual(genes=mutated_genes)


def adaptive_genetic_optimizer(
    config: OptimizationConfig,
    objective_function: Callable[[Dict[str, Any]], float],
    initial_params: Optional[Dict[str, Any]] = None
) -> OptimizationResult:
    """
    적응형 유전 알고리즘 (Adaptive GA)

    특징:
    - 세대가 진행됨에 따라 돌연변이율 감소
    - 정체 시 돌연변이율 증가로 탈출 시도
    - 자동 파라미터 조정
    """
    optimizer = GeneticOptimizer(config)

    # 초기 설정
    original_mutation_rate = config.mutation_rate
    stagnation_counter = 0
    last_best_fitness = float('-inf')

    logger.info("Starting Adaptive Genetic Algorithm")

    # 초기 집단 생성
    optimizer._initialize_population(initial_params)
    optimizer._evaluate_population(objective_function)

    best_individual = max(optimizer.population, key=lambda x: x.fitness)
    best_score = best_individual.fitness
    best_params = best_individual.genes.copy()
    all_results = []

    # 세대 진화
    for generation in range(config.max_iterations):
        optimizer.generation = generation + 1

        # 적응형 돌연변이율 조정
        if generation < config.max_iterations * 0.3:
            # 초기: 높은 탐색
            config.mutation_rate = original_mutation_rate * 1.5
        elif generation < config.max_iterations * 0.7:
            # 중기: 표준
            config.mutation_rate = original_mutation_rate
        else:
            # 후기: 낮은 탐색 (수렴)
            config.mutation_rate = original_mutation_rate * 0.5

        # 정체 감지 시 돌연변이율 증가
        current_best = max(optimizer.population, key=lambda x: x.fitness)
        if current_best.fitness <= last_best_fitness:
            stagnation_counter += 1
            if stagnation_counter > 5:
                config.mutation_rate *= 1.5  # 탈출 시도
        else:
            stagnation_counter = 0

        last_best_fitness = current_best.fitness

        # 진화
        new_population = optimizer._evolve_population()
        optimizer.population = new_population
        optimizer._evaluate_population(objective_function)

        # 최고 개체 추적
        current_best = max(optimizer.population, key=lambda x: x.fitness)

        all_results.append({
            "iteration": generation + 1,
            "parameters": current_best.genes.copy(),
            "score": current_best.fitness,
            "mutation_rate": config.mutation_rate
        })

        if current_best.fitness > best_score:
            best_score = current_best.fitness
            best_params = current_best.genes.copy()
            logger.info(f"Gen {generation + 1}: New best={best_score:.4f}")

    # 원래 설정 복원
    config.mutation_rate = original_mutation_rate

    return OptimizationResult(
        best_parameters=best_params,
        best_score=best_score,
        all_results=all_results,
        total_iterations=generation + 1
    )
