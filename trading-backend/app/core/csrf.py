"""
CSRF Protection Module

Double Submit Cookie 패턴을 사용한 CSRF 토큰 검증.
- 토큰을 쿠키와 헤더에 모두 포함
- 상태 변경 요청(POST, PUT, DELETE)에서 검증
"""

import secrets
from fastapi import Request, HTTPException, status
from fastapi.responses import Response
from typing import Optional


CSRF_TOKEN_LENGTH = 32
CSRF_COOKIE_NAME = "csrf_token"
CSRF_HEADER_NAME = "X-CSRF-Token"
CSRF_COOKIE_MAX_AGE = 3600  # 1 hour


def generate_csrf_token() -> str:
    """
    CSRF 토큰 생성

    Returns:
        32바이트 랜덤 토큰 (URL-safe)
    """
    return secrets.token_urlsafe(CSRF_TOKEN_LENGTH)


def set_csrf_cookie(response: Response, token: str) -> None:
    """
    응답에 CSRF 토큰 쿠키 설정

    Args:
        response: FastAPI Response 객체
        token: CSRF 토큰
    """
    response.set_cookie(
        key=CSRF_COOKIE_NAME,
        value=token,
        max_age=CSRF_COOKIE_MAX_AGE,
        httponly=False,  # JavaScript에서 읽을 수 있어야 함
        secure=False,  # Production에서는 True (HTTPS)
        samesite="strict",  # CSRF 공격 방어
    )


def get_csrf_token_from_cookie(request: Request) -> Optional[str]:
    """
    요청 쿠키에서 CSRF 토큰 추출

    Args:
        request: FastAPI Request 객체

    Returns:
        CSRF 토큰 또는 None
    """
    return request.cookies.get(CSRF_COOKIE_NAME)


def get_csrf_token_from_header(request: Request) -> Optional[str]:
    """
    요청 헤더에서 CSRF 토큰 추출

    Args:
        request: FastAPI Request 객체

    Returns:
        CSRF 토큰 또는 None
    """
    return request.headers.get(CSRF_HEADER_NAME)


def verify_csrf_token(request: Request) -> bool:
    """
    CSRF 토큰 검증

    Double Submit Cookie 패턴:
    - 쿠키의 토큰과 헤더의 토큰이 일치하는지 확인

    Args:
        request: FastAPI Request 객체

    Returns:
        검증 성공 여부
    """
    cookie_token = get_csrf_token_from_cookie(request)
    header_token = get_csrf_token_from_header(request)

    if not cookie_token or not header_token:
        return False

    # Constant-time comparison to prevent timing attacks
    return secrets.compare_digest(cookie_token, header_token)


async def csrf_protect(request: Request) -> None:
    """
    CSRF 보호 의존성 (Dependency)

    상태 변경 요청(POST, PUT, DELETE)에서 사용

    Args:
        request: FastAPI Request 객체

    Raises:
        HTTPException: CSRF 토큰 검증 실패 시
    """
    # GET, HEAD, OPTIONS는 CSRF 보호 불필요
    if request.method in ["GET", "HEAD", "OPTIONS"]:
        return

    # CSRF 토큰 검증
    if not verify_csrf_token(request):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CSRF token validation failed"
        )
