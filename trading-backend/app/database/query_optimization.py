"""
Query Optimization Helpers

Features:
- N+1 쿼리 방지 (Eager Loading)
- 쿼리 성능 분석 (EXPLAIN ANALYZE)
- 데이터베이스 연결 풀 모니터링
- 슬로우 쿼리 로깅
"""

import logging
import time
from typing import List, Optional, Any, Type
from functools import wraps
from contextlib import contextmanager

from sqlalchemy import text, event
from sqlalchemy.orm import Session, joinedload, selectinload, subqueryload
from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.base import Base

logger = logging.getLogger(__name__)


# =======================
# Slow Query Logger
# =======================

class SlowQueryLogger:
    """
    Slow Query Logger

    Features:
    - 느린 쿼리 자동 감지 (기본 1초 이상)
    - EXPLAIN ANALYZE 자동 실행
    - 로그 레벨별 분류
    """

    def __init__(self, slow_query_threshold: float = 1.0):
        """
        Args:
            slow_query_threshold: 느린 쿼리 기준 (초)
        """
        self.slow_query_threshold = slow_query_threshold

    def setup_event_listeners(self, engine: Engine):
        """SQLAlchemy 엔진에 이벤트 리스너 등록"""

        @event.listens_for(engine, "before_cursor_execute")
        def receive_before_cursor_execute(
            conn, cursor, statement, parameters, context, executemany
        ):
            context._query_start_time = time.time()

        @event.listens_for(engine, "after_cursor_execute")
        def receive_after_cursor_execute(
            conn, cursor, statement, parameters, context, executemany
        ):
            total_time = time.time() - context._query_start_time

            if total_time >= self.slow_query_threshold:
                logger.warning(
                    f"⚠️ Slow Query Detected ({total_time:.2f}s):\n"
                    f"Statement: {statement}\n"
                    f"Parameters: {parameters}"
                )

                # PostgreSQL EXPLAIN ANALYZE 자동 실행
                try:
                    if statement.strip().upper().startswith("SELECT"):
                        explain_query = f"EXPLAIN ANALYZE {statement}"
                        result = conn.execute(text(explain_query), parameters)
                        explain_output = "\n".join([row[0] for row in result])

                        logger.warning(
                            f"EXPLAIN ANALYZE Output:\n{explain_output}"
                        )
                except Exception as e:
                    logger.error(f"Failed to run EXPLAIN ANALYZE: {e}")


# =======================
# N+1 Query Prevention
# =======================

class EagerLoadHelper:
    """
    N+1 쿼리 방지 헬퍼

    Features:
    - Relationship eager loading 자동화
    - 자주 사용하는 쿼리 패턴 사전 정의
    """

    @staticmethod
    def load_user_with_relations(
        session: Session,
        user_id: str,
        load_api_keys: bool = False,
        load_positions: bool = False,
        load_trades: bool = False,
        load_settings: bool = False
    ):
        """
        User + 관련 데이터 한번에 로딩 (N+1 방지)

        Args:
            session: DB Session
            user_id: 사용자 ID
            load_api_keys: API 키 로딩 여부
            load_positions: 포지션 로딩 여부
            load_trades: 거래 내역 로딩 여부
            load_settings: 설정 로딩 여부

        Returns:
            User 객체 (관련 데이터 eager loaded)
        """
        from app.models.user import User

        query = session.query(User).filter(User.id == user_id)

        # Eager loading options
        if load_api_keys:
            query = query.options(selectinload(User.api_keys))

        if load_positions:
            query = query.options(selectinload(User.positions))

        if load_trades:
            query = query.options(selectinload(User.trades))

        if load_settings:
            query = query.options(joinedload(User.settings))

        return query.first()

    @staticmethod
    def load_positions_with_user(
        session: Session,
        user_id: str,
        status: Optional[str] = "OPEN"
    ):
        """
        포지션 + User 정보 한번에 로딩

        Args:
            session: DB Session
            user_id: 사용자 ID
            status: 포지션 상태 ("OPEN", "CLOSED", None)

        Returns:
            List[Position]
        """
        from app.models.trading import Position

        query = session.query(Position).filter(Position.user_id == user_id)

        if status:
            query = query.filter(Position.status == status)

        # User 정보 eager loading
        query = query.options(joinedload(Position.user))

        # 최신순 정렬
        query = query.order_by(Position.opened_at.desc())

        return query.all()

    @staticmethod
    def load_trades_with_aggregations(
        session: Session,
        user_id: str,
        symbol: Optional[str] = None,
        limit: int = 100
    ):
        """
        거래 내역 + 집계 데이터 최적화 로딩

        Args:
            session: DB Session
            user_id: 사용자 ID
            symbol: 심볼 (선택)
            limit: 최대 개수

        Returns:
            List[Trade]
        """
        from app.models.trading import Trade

        query = session.query(Trade).filter(Trade.user_id == user_id)

        if symbol:
            query = query.filter(Trade.symbol == symbol)

        # 인덱스 활용 (idx_trades_user_closed_desc)
        query = query.order_by(Trade.closed_at.desc())

        # Limit 적용
        query = query.limit(limit)

        return query.all()

    @staticmethod
    def load_strategy_configs_with_strategy(
        session: Session,
        user_id: str,
        is_active: Optional[bool] = None
    ):
        """
        전략 설정 + 전략 템플릿 한번에 로딩

        Args:
            session: DB Session
            user_id: 사용자 ID
            is_active: 활성 여부

        Returns:
            List[StrategyConfig]
        """
        from app.models.strategy import StrategyConfig

        query = session.query(StrategyConfig).filter(
            StrategyConfig.user_id == user_id
        )

        if is_active is not None:
            query = query.filter(StrategyConfig.is_active == is_active)

        # Strategy 정보 eager loading
        query = query.options(joinedload(StrategyConfig.strategy))

        # 최근 사용순 정렬 (인덱스 활용)
        query = query.order_by(StrategyConfig.last_used_at.desc())

        return query.all()


# =======================
# Query Performance Analyzer
# =======================

def analyze_query_performance(
    session: Session,
    query_statement: str,
    parameters: Optional[dict] = None
):
    """
    쿼리 성능 분석 (EXPLAIN ANALYZE)

    Args:
        session: DB Session
        query_statement: SQL 쿼리
        parameters: 쿼리 파라미터

    Returns:
        EXPLAIN ANALYZE 결과
    """
    try:
        explain_query = f"EXPLAIN (ANALYZE, BUFFERS, VERBOSE) {query_statement}"

        if parameters:
            result = session.execute(text(explain_query), parameters)
        else:
            result = session.execute(text(explain_query))

        explain_output = "\n".join([row[0] for row in result])

        logger.info(f"Query Performance Analysis:\n{explain_output}")

        return explain_output

    except Exception as e:
        logger.error(f"Failed to analyze query: {e}")
        return None


# =======================
# Database Connection Pool Monitor
# =======================

class ConnectionPoolMonitor:
    """
    데이터베이스 연결 풀 모니터링

    Features:
    - 연결 풀 사용률 추적
    - 연결 누수 감지
    - 통계 정보 제공
    """

    @staticmethod
    def get_pool_stats(engine: Engine) -> dict:
        """
        연결 풀 통계 조회

        Args:
            engine: SQLAlchemy Engine

        Returns:
            연결 풀 통계 딕셔너리
        """
        pool = engine.pool

        return {
            "size": pool.size(),
            "checked_in": pool.checkedin(),
            "checked_out": pool.checkedout(),
            "overflow": pool.overflow(),
            "total_connections": pool.size() + pool.overflow(),
            "utilization_pct": round(
                (pool.checkedout() / (pool.size() + pool.overflow())) * 100, 2
            ) if (pool.size() + pool.overflow()) > 0 else 0
        }

    @staticmethod
    def check_connection_leaks(engine: Engine, threshold: float = 0.8):
        """
        연결 누수 감지

        Args:
            engine: SQLAlchemy Engine
            threshold: 경고 임계값 (80%)

        Returns:
            연결 누수 감지 여부
        """
        stats = ConnectionPoolMonitor.get_pool_stats(engine)

        utilization = stats["utilization_pct"] / 100

        if utilization >= threshold:
            logger.warning(
                f"⚠️ High connection pool utilization: {stats['utilization_pct']}%\n"
                f"Checked out: {stats['checked_out']}\n"
                f"Total: {stats['total_connections']}\n"
                f"Possible connection leak!"
            )
            return True

        return False


# =======================
# Decorators
# =======================

def measure_query_time(func):
    """쿼리 실행 시간 측정 데코레이터"""

    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()

        result = func(*args, **kwargs)

        elapsed_time = time.time() - start_time

        if elapsed_time > 1.0:
            logger.warning(
                f"⚠️ Slow operation: {func.__name__} took {elapsed_time:.2f}s"
            )
        else:
            logger.debug(
                f"Query operation: {func.__name__} took {elapsed_time:.4f}s"
            )

        return result

    return wrapper


@contextmanager
def query_timer(operation_name: str):
    """컨텍스트 매니저 형태의 쿼리 타이머"""
    start_time = time.time()

    yield

    elapsed_time = time.time() - start_time

    if elapsed_time > 1.0:
        logger.warning(
            f"⚠️ Slow operation: {operation_name} took {elapsed_time:.2f}s"
        )
    else:
        logger.debug(
            f"Operation: {operation_name} took {elapsed_time:.4f}s"
        )


# =======================
# Database Session Utilities
# =======================

@contextmanager
def optimized_session(session: Session):
    """
    최적화된 데이터베이스 세션 컨텍스트

    Features:
    - 자동 커밋/롤백
    - 에러 핸들링
    - 연결 풀 모니터링
    """
    try:
        yield session
        session.commit()

    except Exception as e:
        session.rollback()
        logger.error(f"Database session error: {e}")
        raise

    finally:
        session.close()


# =======================
# Global Instances
# =======================

# Slow Query Logger (main.py에서 초기화)
slow_query_logger = SlowQueryLogger(slow_query_threshold=1.0)

# Eager Loading Helper
eager_load = EagerLoadHelper()
