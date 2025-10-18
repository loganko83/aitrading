"""
API Wrapper with Stability Enhancements

거래소 API 호출을 안전하게 래핑하는 유틸리티
- Automatic retry with exponential backoff
- Timeout protection
- Circuit breaker pattern
- Graceful error handling
"""

import asyncio
import logging
from typing import Any, Callable, Dict, Optional, TypeVar
from functools import wraps

from app.core.stability import (
    breaker_manager,
    with_async_retry,
    with_timeout,
    RetryStrategy,
    CircuitBreakerOpenError,
    BINANCE_BREAKER,
    OKX_BREAKER
)

logger = logging.getLogger(__name__)

T = TypeVar('T')


class APIError(Exception):
    """Base class for API errors"""
    pass


class RateLimitError(APIError):
    """Rate limit exceeded"""
    pass


class AuthenticationError(APIError):
    """Authentication failed"""
    pass


class ExchangeError(APIError):
    """Exchange-specific error"""
    pass


class NetworkError(APIError):
    """Network connectivity error"""
    pass


def safe_api_call(
    exchange: str = "binance",
    max_attempts: int = 3,
    timeout_seconds: float = 30.0,
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL,
    base_delay: float = 1.0,
    enable_circuit_breaker: bool = True
):
    """
    Decorator for safe API calls with retry, timeout, and circuit breaker

    Usage:
        @safe_api_call(exchange="binance", max_attempts=5, timeout_seconds=30)
        async def fetch_ticker(symbol: str):
            # API call here
            return data

    Features:
    - Automatic retry with exponential backoff
    - Timeout protection
    - Circuit breaker to prevent cascading failures
    - Rate limit handling
    - Comprehensive error logging
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        # Determine circuit breaker name
        breaker_name = BINANCE_BREAKER if exchange.lower() == "binance" else OKX_BREAKER

        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            # Step 1: Check circuit breaker
            if enable_circuit_breaker:
                breaker = breaker_manager.get_or_create(
                    name=breaker_name,
                    failure_threshold=5,
                    recovery_timeout=60,
                    success_threshold=2
                )

                # If circuit is open, fail fast
                if breaker.state.value == "open":
                    logger.warning(
                        f"Circuit breaker for {exchange} is OPEN. "
                        f"Skipping API call to {func.__name__}"
                    )
                    raise CircuitBreakerOpenError(
                        f"{exchange} API is temporarily unavailable. "
                        f"Circuit breaker is open."
                    )

            # Step 2: Execute with retry and timeout
            last_exception = None

            for attempt in range(1, max_attempts + 1):
                try:
                    # Apply timeout
                    result = await asyncio.wait_for(
                        func(*args, **kwargs),
                        timeout=timeout_seconds
                    )

                    # Success - update circuit breaker
                    if enable_circuit_breaker:
                        breaker._on_success()

                    return result

                except asyncio.TimeoutError as e:
                    last_exception = e
                    logger.error(
                        f"{exchange} API call {func.__name__} timed out "
                        f"after {timeout_seconds}s (attempt {attempt}/{max_attempts})"
                    )

                    if attempt == max_attempts:
                        if enable_circuit_breaker:
                            breaker._on_failure()
                        raise NetworkError(
                            f"API call timed out after {timeout_seconds} seconds"
                        ) from e

                except RateLimitError as e:
                    # Rate limit errors require longer backoff
                    last_exception = e
                    if attempt == max_attempts:
                        if enable_circuit_breaker:
                            breaker._on_failure()
                        raise

                    # Use longer delay for rate limits
                    delay = base_delay * (3 ** (attempt - 1))  # More aggressive backoff
                    logger.warning(
                        f"Rate limit hit on {exchange} API {func.__name__} "
                        f"(attempt {attempt}/{max_attempts}). "
                        f"Waiting {delay:.2f}s..."
                    )
                    await asyncio.sleep(delay)

                except (NetworkError, ConnectionError, OSError) as e:
                    # Network errors are retryable
                    last_exception = e
                    if attempt == max_attempts:
                        if enable_circuit_breaker:
                            breaker._on_failure()
                        raise NetworkError(
                            f"Network error after {max_attempts} attempts: {str(e)}"
                        ) from e

                    # Calculate backoff delay
                    if strategy == RetryStrategy.EXPONENTIAL:
                        delay = base_delay * (2 ** (attempt - 1))
                    elif strategy == RetryStrategy.LINEAR:
                        delay = base_delay * attempt
                    else:
                        delay = base_delay

                    logger.warning(
                        f"Network error on {exchange} API {func.__name__} "
                        f"(attempt {attempt}/{max_attempts}). "
                        f"Retrying in {delay:.2f}s... Error: {e}"
                    )
                    await asyncio.sleep(delay)

                except AuthenticationError as e:
                    # Authentication errors are not retryable
                    logger.error(
                        f"Authentication failed for {exchange} API {func.__name__}: {e}"
                    )
                    if enable_circuit_breaker:
                        breaker._on_failure()
                    raise

                except Exception as e:
                    # Unknown errors
                    last_exception = e
                    logger.error(
                        f"Unexpected error in {exchange} API {func.__name__} "
                        f"(attempt {attempt}/{max_attempts}): {e}",
                        exc_info=True
                    )

                    if attempt == max_attempts:
                        if enable_circuit_breaker:
                            breaker._on_failure()
                        raise ExchangeError(
                            f"API call failed after {max_attempts} attempts: {str(e)}"
                        ) from e

                    delay = base_delay * (2 ** (attempt - 1))
                    await asyncio.sleep(delay)

            # Should never reach here
            if enable_circuit_breaker:
                breaker._on_failure()
            raise last_exception

        return wrapper
    return decorator


async def fetch_with_fallback(
    primary_func: Callable[..., T],
    fallback_func: Optional[Callable[..., T]] = None,
    fallback_value: Optional[T] = None,
    *args,
    **kwargs
) -> T:
    """
    Fetch data with automatic fallback

    Usage:
        data = await fetch_with_fallback(
            primary_func=fetch_from_binance,
            fallback_func=fetch_from_cache,
            fallback_value=None,
            symbol="BTCUSDT"
        )
    """

    try:
        return await primary_func(*args, **kwargs)

    except CircuitBreakerOpenError:
        logger.warning(
            f"Circuit breaker is open for {primary_func.__name__}. "
            f"Attempting fallback..."
        )

        if fallback_func:
            try:
                return await fallback_func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Fallback also failed: {e}")
                if fallback_value is not None:
                    return fallback_value
                raise

        elif fallback_value is not None:
            return fallback_value

        else:
            raise

    except Exception as e:
        logger.error(f"Primary function {primary_func.__name__} failed: {e}")

        if fallback_func:
            try:
                logger.info(f"Attempting fallback function...")
                return await fallback_func(*args, **kwargs)
            except Exception as fallback_error:
                logger.error(f"Fallback also failed: {fallback_error}")
                if fallback_value is not None:
                    return fallback_value
                raise

        elif fallback_value is not None:
            logger.info(f"Using fallback value")
            return fallback_value

        else:
            raise


class GracefulDegradation:
    """
    Graceful degradation manager

    서비스 저하 시 우아하게 기능을 축소하는 매니저
    """

    def __init__(self):
        self.degraded_services: Dict[str, bool] = {}
        self.degradation_reasons: Dict[str, str] = {}

    def mark_degraded(self, service: str, reason: str):
        """Mark a service as degraded"""
        self.degraded_services[service] = True
        self.degradation_reasons[service] = reason
        logger.warning(f"Service '{service}' marked as degraded: {reason}")

    def mark_healthy(self, service: str):
        """Mark a service as healthy"""
        if service in self.degraded_services:
            del self.degraded_services[service]
            del self.degradation_reasons[service]
            logger.info(f"Service '{service}' restored to healthy state")

    def is_degraded(self, service: str) -> bool:
        """Check if a service is degraded"""
        return self.degraded_services.get(service, False)

    def get_degradation_reason(self, service: str) -> Optional[str]:
        """Get reason for service degradation"""
        return self.degradation_reasons.get(service)

    def get_all_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all services"""
        return {
            service: {
                "degraded": degraded,
                "reason": self.degradation_reasons.get(service, "")
            }
            for service, degraded in self.degraded_services.items()
        }


# Global degradation manager
degradation_manager = GracefulDegradation()


def get_degradation_manager() -> GracefulDegradation:
    """Get global degradation manager"""
    return degradation_manager


# Example: Binance API wrapper with all safety features
@safe_api_call(
    exchange="binance",
    max_attempts=5,
    timeout_seconds=30,
    strategy=RetryStrategy.EXPONENTIAL,
    enable_circuit_breaker=True
)
async def safe_binance_request(endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Safe Binance API request with retry, timeout, and circuit breaker

    Example:
        data = await safe_binance_request("/api/v3/ticker/price", {"symbol": "BTCUSDT"})
    """
    # This is a placeholder - actual implementation would use ccxt or binance SDK
    # For now, just demonstrate the wrapper pattern
    logger.info(f"Making Binance API request to {endpoint} with params {params}")

    # TODO: Implement actual API call here
    # import ccxt
    # exchange = ccxt.binance()
    # return await exchange.fetch_ticker(symbol)

    raise NotImplementedError("Actual API implementation needed")


# Example: OKX API wrapper
@safe_api_call(
    exchange="okx",
    max_attempts=5,
    timeout_seconds=30,
    strategy=RetryStrategy.EXPONENTIAL,
    enable_circuit_breaker=True
)
async def safe_okx_request(endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Safe OKX API request with retry, timeout, and circuit breaker

    Example:
        data = await safe_okx_request("/api/v5/market/ticker", {"instId": "BTC-USDT"})
    """
    logger.info(f"Making OKX API request to {endpoint} with params {params}")

    # TODO: Implement actual API call here
    raise NotImplementedError("Actual API implementation needed")
