"""
Authentication and Authorization

Features:
- JWT 토큰 검증
- 사용자 인증 미들웨어
- NextAuth 세션 검증
"""

from fastapi import Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
import jwt
from datetime import datetime
import logging

from app.core.config import settings
from app.database.base import get_db
from app.models.user import User, Session as UserSession

logger = logging.getLogger(__name__)

security = HTTPBearer()


def verify_jwt_token(token: str) -> dict:
    """
    JWT 토큰 검증

    Args:
        token: JWT 토큰

    Returns:
        토큰 페이로드

    Raises:
        HTTPException: 토큰이 유효하지 않은 경우
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        return payload

    except jwt.ExpiredSignatureError:
        logger.warning("JWT token expired")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid JWT token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    현재 로그인한 사용자 가져오기

    JWT 토큰 또는 NextAuth 세션 토큰 검증

    Args:
        credentials: Bearer 토큰
        db: 데이터베이스 세션

    Returns:
        User 객체

    Raises:
        HTTPException: 인증 실패 시
    """
    token = credentials.credentials

    try:
        # 1. JWT 토큰 검증 시도
        try:
            payload = verify_jwt_token(token)
            user_id = payload.get("sub")

            if not user_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token payload"
                )

            result = await db.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()

            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )

            logger.info(f"User authenticated via JWT: {user.email}")
            return user

        except HTTPException:
            # JWT 실패 시 NextAuth 세션 토큰 시도
            pass

        # 2. NextAuth 세션 토큰 검증
        result = await db.execute(select(UserSession).where(UserSession.session_token == token))
        session = result.scalar_one_or_none()

        if not session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid session token"
            )

        # 세션 만료 확인
        if session.expires < datetime.utcnow():
            logger.warning(f"Session expired for token: {token[:10]}...")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session has expired"
            )

        result = await db.execute(select(User).where(User.id == session.user_id))
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        logger.info(f"User authenticated via NextAuth session: {user.email}")
        return user

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed"
        )


async def get_optional_user(
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """
    선택적 사용자 인증 (인증 실패 시 None 반환)

    Args:
        authorization: Authorization 헤더
        db: 데이터베이스 세션

    Returns:
        User 객체 또는 None
    """
    if not authorization:
        return None

    try:
        # Bearer 토큰 추출
        if not authorization.startswith("Bearer "):
            return None

        token = authorization.replace("Bearer ", "")

        # HTTPAuthorizationCredentials 생성
        from fastapi.security import HTTPAuthorizationCredentials
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=token
        )

        return await get_current_user(credentials=credentials, db=db)

    except HTTPException:
        return None
    except Exception:
        return None
