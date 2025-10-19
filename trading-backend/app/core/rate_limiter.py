"""
Redis 기반 Rate Limiter

Features:
- Sliding window rate limiting
- Per-user, per-IP, per-endpoint rate limiting
- Automatic cleanup
"""

import logging
from typing import Optional
from fastapi import Request, HTTPException
from datetime import datetime, timedelta

from app.core.redis_client import RedisClient

logger = logging.getLogger(__name__)


class RateLimiter:
    """Redis 기반 Rate Limiter"""

    def __init__(
        self,
        max_requests: int = 100,
        window_seconds: int = 60,
        key_prefix: str = "rate_limit"
    ):
        """
        Args:
            max_requests: 시간 윈도우 내 최대 요청 수
            window_seconds: 시간 윈도우 (초)
            key_prefix: Redis 키 접두사
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.key_prefix = key_prefix

    async def is_allowed(
        self,
        identifier: str,
        endpoint: Optional[str] = None
    ) -> tuple[bool, dict]:
        """
        Rate limit 체크

        Args:
            identifier: 사용자/IP 식별자
            endpoint: 엔드포인트 (선택)

        Returns:
            (허용 여부, 메타데이터)
        """
        try:
            client = await RedisClient.get_client()

            # 캐시 키 생성
            key_parts = [self.key_prefix, identifier]
            if endpoint:
                key_parts.append(endpoint)
            cache_key = ":".join(key_parts)

            # 현재 시간
            now = datetime.utcnow()
            window_start = now - timedelta(seconds=self.window_seconds)

            # 시간 윈도우 내 요청 수 조회
            # Sorted Set 사용 (score = timestamp)
            pipe = client.pipeline()

            # 1. 만료된 요청 삭제
            pipe.zremrangebyscore(
                cache_key,
                0,
                window_start.timestamp()
            )

            # 2. 현재 요청 수 조회
            pipe.zcard(cache_key)

            # 3. 현재 요청 추가
            pipe.zadd(
                cache_key,
                {str(now.timestamp()): now.timestamp()}
            )

            # 4. TTL 설정
            pipe.expire(cache_key, self.window_seconds * 2)

            results = await pipe.execute()

            # 요청 수 (현재 추가 전)
            current_requests = results[1]

            # Rate limit 체크
            allowed = current_requests < self.max_requests

            metadata = {
                "limit": self.max_requests,
                "remaining": max(0, self.max_requests - current_requests - 1),
                "reset_at": int((now + timedelta(seconds=self.window_seconds)).timestamp()),
                "window_seconds": self.window_seconds
            }

            if not allowed:
                logger.warning(
                    f"Rate limit exceeded for {identifier}: "
                    f"{current_requests}/{self.max_requests} in {self.window_seconds}s"
                )

            return allowed, metadata

        except Exception as e:
            logger.error(f"Rate limiter error: {e}")
            # 에러 발생 시 요청 허용 (fail-open)
            return True, {
                "limit": self.max_requests,
                "remaining": self.max_requests,
                "reset_at": 0,
                "window_seconds": self.window_seconds
            }

    async def reset(self, identifier: str, endpoint: Optional[str] = None):
        """Rate limit 리셋"""
        try:
            client = await RedisClient.get_client()

            key_parts = [self.key_prefix, identifier]
            if endpoint:
                key_parts.append(endpoint)
            cache_key = ":".join(key_parts)

            await client.delete(cache_key)
            logger.info(f"Rate limit reset for {identifier}")

        except Exception as e:
            logger.error(f"Rate limit reset error: {e}")


# 전역 rate limiter 인스턴스들
class RateLimiters:
    """Rate limiter 프리셋"""

    # API 엔드포인트별
    STRICT = RateLimiter(max_requests=10, window_seconds=60, key_prefix="rate:strict")
    MODERATE = RateLimiter(max_requests=60, window_seconds=60, key_prefix="rate:moderate")
    LENIENT = RateLimiter(max_requests=300, window_seconds=60, key_prefix="rate:lenient")

    # 특수 목적
    WEBHOOK = RateLimiter(max_requests=1000, window_seconds=60, key_prefix="rate:webhook")
    AUTH = RateLimiter(max_requests=5, window_seconds=300, key_prefix="rate:auth")  # 5분에 5회


async def rate_limit_middleware(
    request: Request,
    limiter: RateLimiter = RateLimiters.MODERATE
):
    """
    Rate limit 미들웨어

    Usage:
        @router.get("/endpoint")
        async def endpoint(
            request: Request,
            _: None = Depends(rate_limit_middleware)
        ):
            ...
    """
    # 식별자 추출 (우선순위: User ID > IP)
    identifier = None

    # 1. User ID (인증된 경우)
    if hasattr(request.state, "user") and request.state.user:
        identifier = f"user:{request.state.user.id}"

    # 2. IP 주소
    if identifier is None:
        client_ip = request.client.host if request.client else "unknown"
        identifier = f"ip:{client_ip}"

    # 엔드포인트 경로
    endpoint = request.url.path

    # Rate limit 체크
    allowed, metadata = await limiter.is_allowed(identifier, endpoint)

    # 헤더 추가
    request.state.rate_limit = metadata

    if not allowed:
        raise HTTPException(
            status_code=429,
            detail={
                "error": "Rate limit exceeded",
                "limit": metadata["limit"],
                "reset_at": metadata["reset_at"],
                "retry_after": metadata["window_seconds"]
            }
        )


def add_rate_limit_headers(response, request: Request):
    """Rate limit 헤더 추가 (응답 미들웨어에서 호출)"""
    if hasattr(request.state, "rate_limit"):
        metadata = request.state.rate_limit
        response.headers["X-RateLimit-Limit"] = str(metadata["limit"])
        response.headers["X-RateLimit-Remaining"] = str(metadata["remaining"])
        response.headers["X-RateLimit-Reset"] = str(metadata["reset_at"])

    return response
