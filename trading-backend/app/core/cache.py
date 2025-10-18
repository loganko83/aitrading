"""
캐싱 및 성능 최적화 시스템

Features:
- In-memory caching with TTL
- Response caching for expensive operations
- LRU cache with size limits
- Cache invalidation strategies
- Performance metrics tracking
"""

import time
import hashlib
import json
from typing import Any, Optional, Callable, Dict, List
from functools import wraps
from collections import OrderedDict
from datetime import datetime, timedelta
import asyncio


class CacheEntry:
    """Cache entry with metadata"""

    def __init__(self, value: Any, ttl_seconds: int = 300):
        self.value = value
        self.created_at = time.time()
        self.expires_at = time.time() + ttl_seconds
        self.hit_count = 0
        self.last_accessed = time.time()

    def is_expired(self) -> bool:
        """Check if cache entry is expired"""
        return time.time() > self.expires_at

    def is_valid(self) -> bool:
        """Check if cache entry is still valid"""
        return not self.is_expired()

    def access(self) -> Any:
        """Access cache entry and update metadata"""
        self.hit_count += 1
        self.last_accessed = time.time()
        return self.value


class LRUCache:
    """LRU (Least Recently Used) Cache with TTL support"""

    def __init__(self, max_size: int = 1000, default_ttl: int = 300):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "size": 0
        }

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if key not in self.cache:
            self.stats["misses"] += 1
            return None

        entry = self.cache[key]

        # Check if expired
        if entry.is_expired():
            self.cache.pop(key)
            self.stats["misses"] += 1
            return None

        # Move to end (most recently used)
        self.cache.move_to_end(key)
        self.stats["hits"] += 1

        return entry.access()

    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None):
        """Set value in cache"""
        ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl

        # Remove if exists (to update position)
        if key in self.cache:
            self.cache.pop(key)

        # Add new entry
        self.cache[key] = CacheEntry(value, ttl)

        # Evict oldest if over max size
        if len(self.cache) > self.max_size:
            oldest_key = next(iter(self.cache))
            self.cache.pop(oldest_key)
            self.stats["evictions"] += 1

        self.stats["size"] = len(self.cache)

    def invalidate(self, key: str):
        """Invalidate specific cache entry"""
        if key in self.cache:
            self.cache.pop(key)
            self.stats["size"] = len(self.cache)

    def invalidate_pattern(self, pattern: str):
        """Invalidate all keys matching pattern"""
        keys_to_remove = [k for k in self.cache.keys() if pattern in k]
        for key in keys_to_remove:
            self.cache.pop(key)
        self.stats["size"] = len(self.cache)

    def clear(self):
        """Clear all cache"""
        self.cache.clear()
        self.stats["size"] = 0

    def cleanup_expired(self):
        """Remove all expired entries"""
        expired_keys = [k for k, v in self.cache.items() if v.is_expired()]
        for key in expired_keys:
            self.cache.pop(key)
        self.stats["size"] = len(self.cache)

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = self.stats["hits"] + self.stats["misses"]
        hit_rate = self.stats["hits"] / total_requests if total_requests > 0 else 0

        return {
            **self.stats,
            "hit_rate": f"{hit_rate * 100:.2f}%",
            "total_requests": total_requests
        }


class CacheManager:
    """Global cache manager with multiple cache instances"""

    def __init__(self):
        # Different caches for different purposes
        self.backtest_cache = LRUCache(max_size=100, default_ttl=1800)  # 30 minutes
        self.market_data_cache = LRUCache(max_size=500, default_ttl=60)  # 1 minute
        self.strategy_cache = LRUCache(max_size=50, default_ttl=3600)  # 1 hour
        self.preset_cache = LRUCache(max_size=20, default_ttl=86400)  # 24 hours
        self.pine_script_cache = LRUCache(max_size=100, default_ttl=3600)  # 1 hour

        # Performance metrics
        self.performance_metrics: List[Dict] = []
        self.max_metrics = 1000

    def get_cache(self, cache_type: str) -> LRUCache:
        """Get specific cache instance"""
        cache_map = {
            "backtest": self.backtest_cache,
            "market_data": self.market_data_cache,
            "strategy": self.strategy_cache,
            "preset": self.preset_cache,
            "pine_script": self.pine_script_cache
        }
        return cache_map.get(cache_type, self.backtest_cache)

    def generate_cache_key(self, *args, **kwargs) -> str:
        """Generate consistent cache key from arguments"""
        # Create a consistent string representation
        key_parts = []

        for arg in args:
            if isinstance(arg, (dict, list)):
                key_parts.append(json.dumps(arg, sort_keys=True))
            else:
                key_parts.append(str(arg))

        for k, v in sorted(kwargs.items()):
            if isinstance(v, (dict, list)):
                key_parts.append(f"{k}={json.dumps(v, sort_keys=True)}")
            else:
                key_parts.append(f"{k}={v}")

        key_string = "|".join(key_parts)

        # Hash for consistent length
        return hashlib.md5(key_string.encode()).hexdigest()

    def record_performance(self, operation: str, duration_ms: float, cache_hit: bool):
        """Record performance metric"""
        metric = {
            "operation": operation,
            "duration_ms": duration_ms,
            "cache_hit": cache_hit,
            "timestamp": datetime.now().isoformat()
        }

        self.performance_metrics.append(metric)

        # Keep only recent metrics
        if len(self.performance_metrics) > self.max_metrics:
            self.performance_metrics = self.performance_metrics[-self.max_metrics:]

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get aggregated performance statistics"""
        if not self.performance_metrics:
            return {"message": "No performance data available"}

        # Group by operation
        operations = {}
        for metric in self.performance_metrics:
            op = metric["operation"]
            if op not in operations:
                operations[op] = {
                    "count": 0,
                    "total_duration_ms": 0,
                    "cache_hits": 0,
                    "cache_misses": 0
                }

            operations[op]["count"] += 1
            operations[op]["total_duration_ms"] += metric["duration_ms"]
            if metric["cache_hit"]:
                operations[op]["cache_hits"] += 1
            else:
                operations[op]["cache_misses"] += 1

        # Calculate averages
        stats = {}
        for op, data in operations.items():
            stats[op] = {
                "count": data["count"],
                "avg_duration_ms": data["total_duration_ms"] / data["count"],
                "cache_hit_rate": f"{(data['cache_hits'] / data['count']) * 100:.2f}%",
                "cache_hits": data["cache_hits"],
                "cache_misses": data["cache_misses"]
            }

        return {
            "operations": stats,
            "total_metrics": len(self.performance_metrics),
            "time_range": {
                "oldest": self.performance_metrics[0]["timestamp"],
                "newest": self.performance_metrics[-1]["timestamp"]
            }
        }

    def get_all_cache_stats(self) -> Dict[str, Any]:
        """Get statistics for all caches"""
        return {
            "backtest": self.backtest_cache.get_stats(),
            "market_data": self.market_data_cache.get_stats(),
            "strategy": self.strategy_cache.get_stats(),
            "preset": self.preset_cache.get_stats(),
            "pine_script": self.pine_script_cache.get_stats()
        }

    def cleanup_all(self):
        """Cleanup expired entries in all caches"""
        self.backtest_cache.cleanup_expired()
        self.market_data_cache.cleanup_expired()
        self.strategy_cache.cleanup_expired()
        self.preset_cache.cleanup_expired()
        self.pine_script_cache.cleanup_expired()

    def clear_all(self):
        """Clear all caches"""
        self.backtest_cache.clear()
        self.market_data_cache.clear()
        self.strategy_cache.clear()
        self.preset_cache.clear()
        self.pine_script_cache.clear()


# Global cache manager instance
cache_manager = CacheManager()


def cached(cache_type: str = "backtest", ttl_seconds: Optional[int] = None):
    """Decorator for caching function results

    Args:
        cache_type: Type of cache to use (backtest, market_data, strategy, preset, pine_script)
        ttl_seconds: Time to live in seconds (overrides cache default)

    Example:
        @cached(cache_type="backtest", ttl_seconds=1800)
        async def run_backtest(symbol: str, strategy: str):
            # Expensive operation
            return result
    """
    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = cache_manager.generate_cache_key(func.__name__, *args, **kwargs)

            # Get appropriate cache
            cache = cache_manager.get_cache(cache_type)

            # Try to get from cache
            start_time = time.time()
            cached_result = cache.get(cache_key)

            if cached_result is not None:
                duration_ms = (time.time() - start_time) * 1000
                cache_manager.record_performance(func.__name__, duration_ms, cache_hit=True)
                return cached_result

            # Cache miss - execute function
            result = await func(*args, **kwargs)
            duration_ms = (time.time() - start_time) * 1000

            # Store in cache
            cache.set(cache_key, result, ttl_seconds)

            cache_manager.record_performance(func.__name__, duration_ms, cache_hit=False)

            return result

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = cache_manager.generate_cache_key(func.__name__, *args, **kwargs)

            # Get appropriate cache
            cache = cache_manager.get_cache(cache_type)

            # Try to get from cache
            start_time = time.time()
            cached_result = cache.get(cache_key)

            if cached_result is not None:
                duration_ms = (time.time() - start_time) * 1000
                cache_manager.record_performance(func.__name__, duration_ms, cache_hit=True)
                return cached_result

            # Cache miss - execute function
            result = func(*args, **kwargs)
            duration_ms = (time.time() - start_time) * 1000

            # Store in cache
            cache.set(cache_key, result, ttl_seconds)

            cache_manager.record_performance(func.__name__, duration_ms, cache_hit=False)

            return result

        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


# Background cleanup task
async def cache_cleanup_task():
    """Background task to cleanup expired cache entries"""
    while True:
        await asyncio.sleep(300)  # Every 5 minutes
        cache_manager.cleanup_all()


# Cache warming functions
def warm_preset_cache():
    """Pre-load preset cache with common presets"""
    from app.core.presets import ALL_PRESETS

    cache = cache_manager.get_cache("preset")

    for preset in ALL_PRESETS:
        cache_key = cache_manager.generate_cache_key("preset", preset.id)
        cache.set(cache_key, preset, ttl_seconds=86400)


def warm_strategy_cache():
    """Pre-load strategy cache with available strategies"""
    strategies = [
        "supertrend",
        "rsi_ema_crossover",
        "macd_stochastic_rsi",
        "ichimoku_cloud",
        "wavetrend_dead_zone",
        "multi_indicator_consensus"
    ]

    cache = cache_manager.get_cache("strategy")

    for strategy in strategies:
        cache_key = cache_manager.generate_cache_key("strategy_info", strategy)
        cache.set(cache_key, {"name": strategy, "available": True}, ttl_seconds=3600)


def initialize_cache():
    """Initialize cache with warm-up data"""
    warm_preset_cache()
    warm_strategy_cache()
