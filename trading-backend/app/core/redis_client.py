"""
Redis Client 및 캐싱 시스템

Features:
- Async Redis 클라이언트
- 캐싱 데코레이터
- TTL 관리
- 자동 직렬화/역직렬화
"""

import json
import pickle
import logging
from typing import Any, Optional, Callable, Union
from functools import wraps
import redis.asyncio as aioredis
from redis.asyncio import Redis
from datetime import timedelta

from app.core.config import settings

logger = logging.getLogger(__name__)


class RedisClient:
    """Redis 클라이언트 싱글톤"""

    _instance: Optional[Redis] = None
    _connection_pool = None

    @classmethod
    async def get_client(cls) -> Redis:
        """Redis 클라이언트 인스턴스 반환 (싱글톤)"""
        if cls._instance is None:
            try:
                # Connection pool 생성
                cls._connection_pool = aioredis.ConnectionPool.from_url(
                    settings.REDIS_URL,
                    max_connections=20,
                    decode_responses=False,  # 바이너리 데이터 지원
                    socket_connect_timeout=5,
                    socket_keepalive=True
                )

                cls._instance = aioredis.Redis(
                    connection_pool=cls._connection_pool
                )

                # 연결 테스트
                await cls._instance.ping()
                logger.info("✅ Redis client initialized successfully")

            except Exception as e:
                logger.error(f"❌ Failed to initialize Redis client: {e}")
                raise

        return cls._instance

    @classmethod
    async def close(cls):
        """Redis 연결 종료"""
        if cls._instance:
            await cls._instance.close()
            await cls._connection_pool.disconnect()
            cls._instance = None
            cls._connection_pool = None
            logger.info("Redis client closed")


class RedisCache:
    """Redis 캐싱 헬퍼 클래스"""

    def __init__(self):
        self.client: Optional[Redis] = None

    async def _get_client(self) -> Redis:
        """Redis 클라이언트 가져오기"""
        if self.client is None:
            self.client = await RedisClient.get_client()
        return self.client

    async def get(
        self,
        key: str,
        use_json: bool = True
    ) -> Optional[Any]:
        """
        캐시에서 값 가져오기

        Args:
            key: 캐시 키
            use_json: JSON 역직렬화 사용 여부 (False면 pickle)

        Returns:
            캐시된 값 또는 None
        """
        try:
            client = await self._get_client()
            value = await client.get(key)

            if value is None:
                return None

            if use_json:
                return json.loads(value)
            else:
                return pickle.loads(value)

        except Exception as e:
            logger.error(f"Redis GET error for key '{key}': {e}")
            return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        use_json: bool = True
    ) -> bool:
        """
        캐시에 값 저장

        Args:
            key: 캐시 키
            value: 저장할 값
            ttl: TTL (초), None이면 만료 없음
            use_json: JSON 직렬화 사용 여부 (False면 pickle)

        Returns:
            성공 여부
        """
        try:
            client = await self._get_client()

            if use_json:
                serialized = json.dumps(value)
            else:
                serialized = pickle.dumps(value)

            if ttl:
                await client.setex(key, ttl, serialized)
            else:
                await client.set(key, serialized)

            return True

        except Exception as e:
            logger.error(f"Redis SET error for key '{key}': {e}")
            return False

    async def delete(self, key: str) -> bool:
        """캐시 키 삭제"""
        try:
            client = await self._get_client()
            await client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Redis DELETE error for key '{key}': {e}")
            return False

    async def exists(self, key: str) -> bool:
        """캐시 키 존재 여부 확인"""
        try:
            client = await self._get_client()
            return await client.exists(key) > 0
        except Exception as e:
            logger.error(f"Redis EXISTS error for key '{key}': {e}")
            return False

    async def expire(self, key: str, ttl: int) -> bool:
        """캐시 키 TTL 설정"""
        try:
            client = await self._get_client()
            await client.expire(key, ttl)
            return True
        except Exception as e:
            logger.error(f"Redis EXPIRE error for key '{key}': {e}")
            return False

    async def ttl(self, key: str) -> int:
        """캐시 키 남은 TTL 조회 (초)"""
        try:
            client = await self._get_client()
            return await client.ttl(key)
        except Exception as e:
            logger.error(f"Redis TTL error for key '{key}': {e}")
            return -1

    async def clear_pattern(self, pattern: str) -> int:
        """
        패턴 매칭으로 캐시 삭제

        Args:
            pattern: Redis 패턴 (예: "market:*", "user:123:*")

        Returns:
            삭제된 키 개수
        """
        try:
            client = await self._get_client()
            keys = []
            async for key in client.scan_iter(match=pattern):
                keys.append(key)

            if keys:
                await client.delete(*keys)
                logger.info(f"Cleared {len(keys)} keys matching pattern '{pattern}'")
                return len(keys)

            return 0

        except Exception as e:
            logger.error(f"Redis CLEAR_PATTERN error for pattern '{pattern}': {e}")
            return 0

    async def increment(self, key: str, amount: int = 1) -> int:
        """
        카운터 증가

        Args:
            key: 카운터 키
            amount: 증가량

        Returns:
            증가 후 값
        """
        try:
            client = await self._get_client()
            return await client.incrby(key, amount)
        except Exception as e:
            logger.error(f"Redis INCREMENT error for key '{key}': {e}")
            return 0

    async def decrement(self, key: str, amount: int = 1) -> int:
        """카운터 감소"""
        try:
            client = await self._get_client()
            return await client.decrby(key, amount)
        except Exception as e:
            logger.error(f"Redis DECREMENT error for key '{key}': {e}")
            return 0


# 전역 캐시 인스턴스
redis_cache = RedisCache()


def cached(
    ttl: int = 300,
    key_prefix: str = "",
    use_json: bool = True
):
    """
    함수 결과 캐싱 데코레이터

    Usage:
        @cached(ttl=60, key_prefix="market")
        async def get_market_data(symbol: str):
            # 비용이 큰 작업
            return data

    Args:
        ttl: 캐시 TTL (초)
        key_prefix: 캐시 키 접두사
        use_json: JSON 직렬화 사용 여부
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 캐시 키 생성
            cache_key_parts = [key_prefix or func.__name__]

            # args를 캐시 키에 포함
            if args:
                cache_key_parts.extend(str(arg) for arg in args)

            # kwargs를 캐시 키에 포함 (정렬하여 일관성 보장)
            if kwargs:
                sorted_kwargs = sorted(kwargs.items())
                cache_key_parts.extend(f"{k}={v}" for k, v in sorted_kwargs)

            cache_key = ":".join(cache_key_parts)

            # 캐시 조회
            cached_value = await redis_cache.get(cache_key, use_json=use_json)

            if cached_value is not None:
                logger.debug(f"Cache HIT: {cache_key}")
                return cached_value

            # 캐시 미스 - 함수 실행
            logger.debug(f"Cache MISS: {cache_key}")
            result = await func(*args, **kwargs)

            # 결과 캐싱
            await redis_cache.set(cache_key, result, ttl=ttl, use_json=use_json)

            return result

        return wrapper
    return decorator


async def invalidate_cache(pattern: str):
    """
    캐시 무효화

    Usage:
        await invalidate_cache("market:*")  # 모든 시장 데이터 캐시 삭제
    """
    count = await redis_cache.clear_pattern(pattern)
    logger.info(f"Invalidated {count} cache entries matching '{pattern}'")
    return count


async def get_or_set_cache(
    key: str,
    factory: Callable,
    ttl: int = 300,
    use_json: bool = True
) -> Any:
    """
    캐시 조회 또는 생성

    Args:
        key: 캐시 키
        factory: 캐시 미스 시 값을 생성하는 함수
        ttl: TTL (초)
        use_json: JSON 직렬화 사용 여부

    Returns:
        캐시된 값 또는 새로 생성된 값
    """
    # 캐시 조회
    value = await redis_cache.get(key, use_json=use_json)

    if value is not None:
        return value

    # 캐시 미스 - 값 생성
    value = await factory() if callable(factory) else factory

    # 캐싱
    await redis_cache.set(key, value, ttl=ttl, use_json=use_json)

    return value
