"""
Rate Limiting Middleware
DDoS 방지 및 API 남용 방지를 위한 Rate Limiter
"""

from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request, Response
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)

# Rate Limiter 초기화
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://",  # 프로덕션에서는 Redis 사용 권장
    headers_enabled=True,
)

# Rate Limit 설정
RATE_LIMITS = {
    # 인증 관련 - 엄격한 제한
    "auth": "5 per minute",

    # API 키 관리 - 중간 수준 제한
    "accounts_register": "10 per hour",
    "accounts_list": "60 per hour",
    "accounts_modify": "30 per hour",

    # Webhook - 높은 빈도 허용
    "webhook": "100 per minute",

    # 조회 API - 높은 빈도 허용
    "balance_check": "120 per hour",
    "positions_check": "120 per hour",

    # 일반 API
    "general": "100 per hour",
}


def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> Response:
    """
    Rate Limit 초과 시 커스텀 에러 응답
    """
    logger.warning(
        f"Rate limit exceeded: {request.client.host} - {request.url.path}"
    )

    return JSONResponse(
        status_code=429,
        content={
            "error": "rate_limit_exceeded",
            "message": "요청 횟수 제한을 초과했습니다. 잠시 후 다시 시도해주세요.",
            "detail": f"Rate limit: {exc.detail}",
            "retry_after": getattr(exc, "retry_after", None)
        },
        headers={
            "Retry-After": str(getattr(exc, "retry_after", 60))
        }
    )


def get_user_identifier(request: Request) -> str:
    """
    사용자 식별자 반환 (IP 또는 User ID)
    인증된 사용자는 User ID로, 비인증은 IP로 식별
    """
    # Authorization 헤더에서 사용자 정보 추출 시도
    auth_header = request.headers.get("authorization")
    if auth_header and auth_header.startswith("Bearer "):
        # JWT 토큰에서 user_id 추출 (옵션)
        # 현재는 IP 기반으로만 처리
        pass

    # IP 주소 반환
    return get_remote_address(request)


# 프로덕션 환경에서 Redis 사용 시
def get_redis_limiter():
    """
    Redis 기반 Rate Limiter (프로덕션 권장)

    설정 방법:
    1. pip install redis
    2. REDIS_URL 환경변수 설정: redis://localhost:6379
    3. 이 함수로 limiter 교체
    """
    import os
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")

    return Limiter(
        key_func=get_remote_address,
        default_limits=["200 per day", "50 per hour"],
        storage_uri=redis_url,
        headers_enabled=True,
    )
