"""
Stability Enhancement System

안정성 강화 시스템 - 재시도, 타임아웃, 서킷 브레이커, 에러 복구
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, Optional, TypeVar, Union
from functools import wraps
import random

logger = logging.getLogger(__name__)

T = TypeVar('T')


class CircuitState(str, Enum):
    """Circuit breaker states"""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failure detected, blocking requests
    HALF_OPEN = "half_open"  # Testing if service recovered


class RetryStrategy(str, Enum):
    """Retry strategies"""
    EXPONENTIAL = "exponential"  # Exponential backoff
    LINEAR = "linear"  # Linear backoff
    CONSTANT = "constant"  # Constant delay
    FIBONACCI = "fibonacci"  # Fibonacci backoff


class CircuitBreaker:
    """
    Circuit Breaker Pattern Implementation

    장애 확산 방지를 위한 서킷 브레이커 패턴
    - CLOSED: 정상 작동
    - OPEN: 장애 감지, 요청 차단 (빠른 실패)
    - HALF_OPEN: 복구 테스트 중
    """

    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,  # 5번 실패시 OPEN
        recovery_timeout: int = 60,  # 60초 후 HALF_OPEN
        success_threshold: int = 2,  # 2번 성공시 CLOSED
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.success_threshold = success_threshold

        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.last_state_change: datetime = datetime.now()

    def call(self, func: Callable[..., T], *args, **kwargs) -> T:
        """Execute function with circuit breaker protection"""

        # Check if we should transition from OPEN to HALF_OPEN
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                logger.info(f"Circuit breaker [{self.name}]: OPEN → HALF_OPEN (testing recovery)")
                self.state = CircuitState.HALF_OPEN
                self.success_count = 0
            else:
                # Still OPEN, reject immediately
                raise CircuitBreakerOpenError(
                    f"Circuit breaker [{self.name}] is OPEN. "
                    f"Will retry at {self._get_next_retry_time()}"
                )

        try:
            # Execute function
            result = func(*args, **kwargs)
            self._on_success()
            return result

        except Exception as e:
            self._on_failure()
            raise

    async def call_async(self, func: Callable[..., T], *args, **kwargs) -> T:
        """Execute async function with circuit breaker protection"""

        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                logger.info(f"Circuit breaker [{self.name}]: OPEN → HALF_OPEN")
                self.state = CircuitState.HALF_OPEN
                self.success_count = 0
            else:
                raise CircuitBreakerOpenError(
                    f"Circuit breaker [{self.name}] is OPEN. "
                    f"Will retry at {self._get_next_retry_time()}"
                )

        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise

    def _on_success(self):
        """Handle successful execution"""
        self.failure_count = 0

        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            logger.info(
                f"Circuit breaker [{self.name}]: Success in HALF_OPEN "
                f"({self.success_count}/{self.success_threshold})"
            )

            if self.success_count >= self.success_threshold:
                logger.info(f"Circuit breaker [{self.name}]: HALF_OPEN → CLOSED (recovered)")
                self.state = CircuitState.CLOSED
                self.success_count = 0
                self.last_state_change = datetime.now()

    def _on_failure(self):
        """Handle failed execution"""
        self.failure_count += 1
        self.last_failure_time = datetime.now()

        if self.state == CircuitState.HALF_OPEN:
            # Failed during recovery test, go back to OPEN
            logger.warning(
                f"Circuit breaker [{self.name}]: HALF_OPEN → OPEN "
                f"(recovery test failed)"
            )
            self.state = CircuitState.OPEN
            self.last_state_change = datetime.now()

        elif self.state == CircuitState.CLOSED:
            if self.failure_count >= self.failure_threshold:
                logger.error(
                    f"Circuit breaker [{self.name}]: CLOSED → OPEN "
                    f"({self.failure_count} failures)"
                )
                self.state = CircuitState.OPEN
                self.last_state_change = datetime.now()

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt recovery"""
        if self.last_failure_time is None:
            return False

        elapsed = (datetime.now() - self.last_failure_time).total_seconds()
        return elapsed >= self.recovery_timeout

    def _get_next_retry_time(self) -> str:
        """Get next retry time as string"""
        if self.last_failure_time is None:
            return "unknown"

        next_retry = self.last_failure_time + timedelta(seconds=self.recovery_timeout)
        return next_retry.strftime("%Y-%m-%d %H:%M:%S")

    def get_status(self) -> Dict[str, Any]:
        """Get current circuit breaker status"""
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "last_failure_time": self.last_failure_time.isoformat() if self.last_failure_time else None,
            "last_state_change": self.last_state_change.isoformat(),
            "next_retry_time": self._get_next_retry_time() if self.state == CircuitState.OPEN else None
        }


class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is open"""
    pass


class RetryConfig:
    """Retry configuration"""

    def __init__(
        self,
        max_attempts: int = 3,
        strategy: RetryStrategy = RetryStrategy.EXPONENTIAL,
        base_delay: float = 1.0,  # seconds
        max_delay: float = 60.0,  # seconds
        exponential_base: float = 2.0,
        jitter: bool = True,  # Add randomness to prevent thundering herd
        retryable_exceptions: Optional[tuple] = None
    ):
        self.max_attempts = max_attempts
        self.strategy = strategy
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
        self.retryable_exceptions = retryable_exceptions or (Exception,)

    def get_delay(self, attempt: int) -> float:
        """Calculate delay for given attempt number"""

        if self.strategy == RetryStrategy.CONSTANT:
            delay = self.base_delay

        elif self.strategy == RetryStrategy.LINEAR:
            delay = self.base_delay * attempt

        elif self.strategy == RetryStrategy.EXPONENTIAL:
            delay = self.base_delay * (self.exponential_base ** (attempt - 1))

        elif self.strategy == RetryStrategy.FIBONACCI:
            delay = self.base_delay * self._fibonacci(attempt)

        else:
            delay = self.base_delay

        # Cap at max_delay
        delay = min(delay, self.max_delay)

        # Add jitter to prevent thundering herd
        if self.jitter:
            delay = delay * (0.5 + random.random())  # 50-150% of delay

        return delay

    @staticmethod
    def _fibonacci(n: int) -> int:
        """Calculate nth Fibonacci number"""
        if n <= 1:
            return n
        a, b = 0, 1
        for _ in range(n - 1):
            a, b = b, a + b
        return b


def with_retry(
    max_attempts: int = 3,
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    jitter: bool = True,
    retryable_exceptions: Optional[tuple] = None
):
    """
    Decorator for automatic retry with exponential backoff

    Usage:
        @with_retry(max_attempts=5, strategy=RetryStrategy.EXPONENTIAL)
        def unstable_function():
            # May fail, will be retried
            pass
    """

    config = RetryConfig(
        max_attempts=max_attempts,
        strategy=strategy,
        base_delay=base_delay,
        max_delay=max_delay,
        jitter=jitter,
        retryable_exceptions=retryable_exceptions
    )

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            last_exception = None

            for attempt in range(1, config.max_attempts + 1):
                try:
                    return func(*args, **kwargs)

                except config.retryable_exceptions as e:
                    last_exception = e

                    if attempt == config.max_attempts:
                        logger.error(
                            f"Function {func.__name__} failed after {config.max_attempts} attempts: {e}"
                        )
                        raise

                    delay = config.get_delay(attempt)
                    logger.warning(
                        f"Function {func.__name__} failed (attempt {attempt}/{config.max_attempts}). "
                        f"Retrying in {delay:.2f}s... Error: {e}"
                    )
                    time.sleep(delay)

            # Should never reach here, but just in case
            raise last_exception

        return wrapper
    return decorator


def with_async_retry(
    max_attempts: int = 3,
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    jitter: bool = True,
    retryable_exceptions: Optional[tuple] = None
):
    """
    Async decorator for automatic retry with exponential backoff

    Usage:
        @with_async_retry(max_attempts=5)
        async def unstable_async_function():
            # May fail, will be retried
            pass
    """

    config = RetryConfig(
        max_attempts=max_attempts,
        strategy=strategy,
        base_delay=base_delay,
        max_delay=max_delay,
        jitter=jitter,
        retryable_exceptions=retryable_exceptions
    )

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            last_exception = None

            for attempt in range(1, config.max_attempts + 1):
                try:
                    return await func(*args, **kwargs)

                except config.retryable_exceptions as e:
                    last_exception = e

                    if attempt == config.max_attempts:
                        logger.error(
                            f"Async function {func.__name__} failed after {config.max_attempts} attempts: {e}"
                        )
                        raise

                    delay = config.get_delay(attempt)
                    logger.warning(
                        f"Async function {func.__name__} failed (attempt {attempt}/{config.max_attempts}). "
                        f"Retrying in {delay:.2f}s... Error: {e}"
                    )
                    await asyncio.sleep(delay)

            raise last_exception

        return wrapper
    return decorator


def with_timeout(seconds: float):
    """
    Decorator for function timeout

    Usage:
        @with_timeout(30)
        async def slow_function():
            # Will timeout after 30 seconds
            pass
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            try:
                return await asyncio.wait_for(
                    func(*args, **kwargs),
                    timeout=seconds
                )
            except asyncio.TimeoutError:
                logger.error(f"Function {func.__name__} timed out after {seconds}s")
                raise TimeoutError(
                    f"Operation timed out after {seconds} seconds"
                )

        return wrapper
    return decorator


class CircuitBreakerManager:
    """
    Global circuit breaker manager

    Usage:
        breaker_manager = CircuitBreakerManager()

        @breaker_manager.protect("api_service")
        async def call_api():
            # Protected by circuit breaker
            pass
    """

    def __init__(self):
        self.breakers: Dict[str, CircuitBreaker] = {}

    def get_or_create(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        success_threshold: int = 2
    ) -> CircuitBreaker:
        """Get existing circuit breaker or create new one"""

        if name not in self.breakers:
            self.breakers[name] = CircuitBreaker(
                name=name,
                failure_threshold=failure_threshold,
                recovery_timeout=recovery_timeout,
                success_threshold=success_threshold
            )

        return self.breakers[name]

    def protect(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        success_threshold: int = 2
    ):
        """
        Decorator for circuit breaker protection

        Usage:
            @breaker_manager.protect("binance_api")
            async def fetch_binance_data():
                # Protected
                pass
        """

        def decorator(func: Callable[..., T]) -> Callable[..., T]:
            breaker = self.get_or_create(
                name=name,
                failure_threshold=failure_threshold,
                recovery_timeout=recovery_timeout,
                success_threshold=success_threshold
            )

            @wraps(func)
            async def wrapper(*args, **kwargs) -> T:
                return await breaker.call_async(func, *args, **kwargs)

            return wrapper
        return decorator

    def get_all_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all circuit breakers"""
        return {
            name: breaker.get_status()
            for name, breaker in self.breakers.items()
        }

    def reset(self, name: str):
        """Reset a circuit breaker to CLOSED state"""
        if name in self.breakers:
            breaker = self.breakers[name]
            breaker.state = CircuitState.CLOSED
            breaker.failure_count = 0
            breaker.success_count = 0
            breaker.last_state_change = datetime.now()
            logger.info(f"Circuit breaker [{name}] manually reset to CLOSED")

    def reset_all(self):
        """Reset all circuit breakers"""
        for name in self.breakers:
            self.reset(name)


# Global circuit breaker manager instance
breaker_manager = CircuitBreakerManager()


# Pre-configured circuit breakers for common services
BINANCE_BREAKER = "binance_api"
OKX_BREAKER = "okx_api"
DATABASE_BREAKER = "database"
CACHE_BREAKER = "cache"


def get_breaker_manager() -> CircuitBreakerManager:
    """Get global circuit breaker manager"""
    return breaker_manager
