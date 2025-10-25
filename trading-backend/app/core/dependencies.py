"""
Authentication Dependencies for FastAPI

JWT 토큰 기반 인증 의존성 함수들을 제공합니다.
"""

from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.base import get_db
from app.core.jwt_service import verify_token
from app.models.user import User


# HTTPBearer 스키마 정의 (Authorization: Bearer <token>)
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    JWT 토큰을 검증하고 현재 사용자 정보를 반환합니다.

    Args:
        credentials: Authorization 헤더에서 추출한 Bearer 토큰
        db: 데이터베이스 세션

    Returns:
        User: 인증된 사용자 객체

    Raises:
        HTTPException: 토큰이 유효하지 않거나 사용자를 찾을 수 없는 경우
    """
    # Authorization 헤더가 없는 경우는 HTTPBearer가 자동으로 처리
    token = credentials.credentials

    # JWT 토큰 검증
    payload = verify_token(token, token_type="access")
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않거나 만료된 토큰입니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 토큰에서 사용자 ID 추출
    user_id: Optional[str] = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="토큰에 사용자 정보가 없습니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 데이터베이스에서 사용자 조회
    from sqlalchemy import select
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="사용자를 찾을 수 없습니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    현재 사용자가 활성 상태인지 확인합니다.

    Args:
        current_user: get_current_user에서 반환된 사용자

    Returns:
        User: 활성 상태인 사용자 객체

    Raises:
        HTTPException: 사용자가 비활성 상태인 경우
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="비활성 사용자입니다. 계정을 활성화해주세요."
        )

    return current_user


async def get_user_id(
    current_user: User = Depends(get_current_user)
) -> str:
    """
    현재 사용자의 ID만 반환하는 간편 의존성입니다.

    Args:
        current_user: get_current_user에서 반환된 사용자

    Returns:
        str: 사용자 ID
    """
    return current_user.id
