"""Authentication API endpoints - 회원가입, 로그인, 2FA 검증"""

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, EmailStr, Field
import uuid

from app.database.base import get_db
from app.models.user import User
from app.core.security import hash_password, verify_password
from app.core.jwt_service import (
    create_access_token,
    create_refresh_token,
    verify_token,
    refresh_access_token
)
from app.core.totp_service import (
    setup_2fa_for_user,
    verify_2fa_setup,
    verify_2fa_login
)
from app.core.dependencies import get_current_user, get_current_active_user, get_user_id
from app.core.redis_client import redis_cache


router = APIRouter(prefix="/auth", tags=["Authentication"])


# ==================== Pydantic Models ====================

class RegisterRequest(BaseModel):
    """회원가입 요청"""
    email: EmailStr = Field(..., description="사용자 이메일")
    password: str = Field(..., min_length=8, max_length=128, description="비밀번호 (최소 8자)")
    name: Optional[str] = Field(None, max_length=100, description="사용자 이름 (선택)")

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "SecurePassword123!",
                "name": "홍길동"
            }
        }


class RegisterResponse(BaseModel):
    """회원가입 응답"""
    success: bool
    message: str
    user_id: str
    email: str
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"


class LoginRequest(BaseModel):
    """로그인 요청"""
    email: EmailStr = Field(..., description="사용자 이메일")
    password: str = Field(..., description="비밀번호")
    totp_code: Optional[str] = Field(None, min_length=6, max_length=6, description="2FA 코드 (2FA 활성화 시 필수)")

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "SecurePassword123!",
                "totp_code": "123456"
            }
        }


class LoginResponse(BaseModel):
    """로그인 응답"""
    success: bool
    message: str
    user_id: str
    email: str
    requires_2fa: bool
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    token_type: str = "Bearer"


class Setup2FAResponse(BaseModel):
    """2FA 설정 응답"""
    success: bool
    message: str
    qr_code_base64: str
    provisioning_uri: str
    encrypted_secret: str
    instructions: list[str]


class Verify2FARequest(BaseModel):
    """2FA 검증 요청"""
    totp_code: str = Field(..., min_length=6, max_length=6, description="인증 앱에서 생성된 6자리 코드")

    class Config:
        json_schema_extra = {
            "example": {
                "totp_code": "123456"
            }
        }


class Verify2FAResponse(BaseModel):
    """2FA 검증 응답"""
    success: bool
    message: str
    is_2fa_enabled: bool


class RefreshTokenRequest(BaseModel):
    """토큰 갱신 요청"""
    refresh_token: str = Field(..., description="Refresh Token")


class RefreshTokenResponse(BaseModel):
    """토큰 갱신 응답"""
    success: bool
    message: str
    access_token: str
    token_type: str = "Bearer"


class LogoutRequest(BaseModel):
    """로그아웃 요청"""
    refresh_token: Optional[str] = Field(None, description="Refresh Token (선택)")


class LogoutResponse(BaseModel):
    """로그아웃 응답"""
    success: bool
    message: str


# ==================== Helper Functions ====================

async def db_commit(db):
    """데이터베이스 커밋 (SQLite/PostgreSQL 호환)"""
    from app.database.base import is_sqlite

    if is_sqlite:
        db.commit()
    else:
        await db_commit(db)


async def db_refresh(db, instance):
    """데이터베이스 객체 새로고침 (SQLite/PostgreSQL 호환)"""
    from app.database.base import is_sqlite

    if is_sqlite:
        db.refresh(instance)
    else:
        await db.refresh(instance)


async def get_user_by_email(db, email: str) -> Optional[User]:
    """이메일로 사용자 조회 (SQLite/PostgreSQL 호환)"""
    from app.database.base import is_sqlite
    from sqlalchemy.orm import Session

    if is_sqlite:
        # SQLite: 동기 방식
        result = db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()
    else:
        # PostgreSQL: 비동기 방식
        result = await db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()


async def get_user_by_id(db, user_id: str) -> Optional[User]:
    """ID로 사용자 조회 (SQLite/PostgreSQL 호환)"""
    from app.database.base import is_sqlite

    if is_sqlite:
        # SQLite: 동기 방식
        result = db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()
    else:
        # PostgreSQL: 비동기 방식
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()


# ==================== API Endpoints ====================

@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: RegisterRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    회원가입

    - **email**: 사용자 이메일 (필수)
    - **password**: 비밀번호 최소 8자 (필수)
    - **name**: 사용자 이름 (선택)

    Returns:
    - JWT Access Token (30분)
    - JWT Refresh Token (7일)
    """
    # 이메일 중복 확인
    existing_user = await get_user_by_email(db, request.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미 사용 중인 이메일입니다."
        )

    # 비밀번호 해싱
    hashed_password = hash_password(request.password)

    # 사용자 생성
    new_user = User(
        id=str(uuid.uuid4()),
        email=request.email,
        name=request.name,
        password=hashed_password,
        is_active=True,
        is_2fa_enabled=False
    )

    db.add(new_user)
    await db_commit(db)
    await db_refresh(db, new_user)

    # JWT 토큰 생성
    access_token = create_access_token(data={"sub": new_user.id, "email": new_user.email})
    refresh_token = create_refresh_token(data={"sub": new_user.id})

    return RegisterResponse(
        success=True,
        message="회원가입이 완료되었습니다.",
        user_id=new_user.id,
        email=new_user.email,
        access_token=access_token,
        refresh_token=refresh_token
    )


@router.post("/login", response_model=LoginResponse)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    로그인

    - **email**: 사용자 이메일
    - **password**: 비밀번호
    - **totp_code**: 2FA 코드 (2FA 활성화된 경우 필수)

    Returns:
    - JWT Access Token (2FA 완료 시)
    - JWT Refresh Token (2FA 완료 시)
    - requires_2fa: True면 2FA 코드 필요
    """
    # 사용자 조회
    user = await get_user_by_email(db, request.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="이메일 또는 비밀번호가 올바르지 않습니다."
        )

    # 비활성화된 계정 확인
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="비활성화된 계정입니다. 관리자에게 문의하세요."
        )

    # 비밀번호 검증
    if not verify_password(request.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="이메일 또는 비밀번호가 올바르지 않습니다."
        )

    # 2FA 활성화 여부 확인
    if user.is_2fa_enabled:
        # 2FA 코드가 제공되지 않음
        if not request.totp_code:
            return LoginResponse(
                success=False,
                message="2단계 인증이 필요합니다. TOTP 코드를 입력하세요.",
                user_id=user.id,
                email=user.email,
                requires_2fa=True
            )

        # 2FA 코드 검증
        is_valid_totp = verify_2fa_login(user.totp_secret, request.totp_code)
        if not is_valid_totp:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="2FA 코드가 올바르지 않습니다."
            )

    # JWT 토큰 생성
    access_token = create_access_token(data={"sub": user.id, "email": user.email})
    refresh_token = create_refresh_token(data={"sub": user.id})

    return LoginResponse(
        success=True,
        message="로그인 성공",
        user_id=user.id,
        email=user.email,
        requires_2fa=False,
        access_token=access_token,
        refresh_token=refresh_token
    )


@router.post("/2fa/setup", response_model=Setup2FAResponse)
async def setup_2fa(
    db: AsyncSession = Depends(get_db),
    current_user_id: str = Depends(get_user_id)
):
    """
    2FA 설정 시작

    - QR 코드 생성
    - 인증 앱에 스캔
    - 설정 완료는 /2fa/verify로 확인

    Returns:
    - QR Code (Base64 이미지)
    - Provisioning URI
    - 암호화된 Secret (DB 저장용)
    """
    # 사용자 조회
    user = await get_user_by_id(db, current_user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자를 찾을 수 없습니다."
        )

    # 이미 2FA 활성화된 경우
    if user.is_2fa_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미 2FA가 활성화되어 있습니다."
        )

    # 2FA 설정 데이터 생성
    setup_data = setup_2fa_for_user(user.email)

    # 암호화된 Secret을 DB에 임시 저장 (아직 활성화 안함)
    user.totp_secret = setup_data["encrypted_secret"]
    await db.commit()

    return Setup2FAResponse(
        success=True,
        message="2FA 설정을 시작합니다. QR 코드를 인증 앱으로 스캔하세요.",
        qr_code_base64=setup_data["qr_code_base64"],
        provisioning_uri=setup_data["provisioning_uri"],
        encrypted_secret=setup_data["encrypted_secret"],
        instructions=[
            "1. Google Authenticator 또는 Authy 앱을 설치하세요.",
            "2. QR 코드를 스캔하세요.",
            "3. 인증 앱에서 생성된 6자리 코드를 /2fa/verify로 전송하세요.",
            "4. 검증 성공 시 2FA가 활성화됩니다."
        ]
    )


@router.post("/2fa/verify", response_model=Verify2FAResponse)
async def verify_2fa(
    request: Verify2FARequest,
    db: AsyncSession = Depends(get_db),
    current_user_id: str = Depends(get_user_id)
):
    """
    2FA 설정 검증 및 활성화

    - 인증 앱에서 생성된 6자리 코드 확인
    - 검증 성공 시 2FA 활성화

    Args:
    - **totp_code**: 인증 앱에서 생성된 6자리 코드

    Returns:
    - 2FA 활성화 여부
    """
    # 사용자 조회
    user = await get_user_by_id(db, current_user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자를 찾을 수 없습니다."
        )

    # TOTP Secret이 없는 경우
    if not user.totp_secret:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="2FA 설정을 먼저 시작하세요. /2fa/setup을 호출하세요."
        )

    # TOTP 코드 검증 (설정 중이므로 wider window 사용)
    is_valid = verify_2fa_setup(user.totp_secret, request.totp_code)

    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="TOTP 코드가 올바르지 않습니다. 다시 시도하세요."
        )

    # 2FA 활성화
    user.is_2fa_enabled = True
    await db.commit()

    return Verify2FAResponse(
        success=True,
        message="2FA가 성공적으로 활성화되었습니다!",
        is_2fa_enabled=True
    )


@router.post("/2fa/disable", response_model=Verify2FAResponse)
async def disable_2fa(
    request: Verify2FARequest,
    db: AsyncSession = Depends(get_db),
    current_user_id: str = Depends(get_user_id)
):
    """
    2FA 비활성화

    - TOTP 코드로 본인 확인 후 2FA 비활성화

    Args:
    - **totp_code**: 인증 앱에서 생성된 6자리 코드

    Returns:
    - 2FA 비활성화 확인
    """
    # 사용자 조회
    user = await get_user_by_id(db, current_user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자를 찾을 수 없습니다."
        )

    # 2FA가 비활성화된 경우
    if not user.is_2fa_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="2FA가 이미 비활성화되어 있습니다."
        )

    # TOTP 코드 검증 (본인 확인)
    is_valid = verify_2fa_login(user.totp_secret, request.totp_code)

    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="TOTP 코드가 올바르지 않습니다."
        )

    # 2FA 비활성화 및 Secret 제거
    user.is_2fa_enabled = False
    user.totp_secret = None
    await db.commit()

    return Verify2FAResponse(
        success=True,
        message="2FA가 비활성화되었습니다.",
        is_2fa_enabled=False
    )


@router.post("/refresh", response_model=RefreshTokenResponse)
async def refresh_token(request: RefreshTokenRequest):
    """
    Access Token 갱신

    - Refresh Token으로 새 Access Token 발급
    - Refresh Token은 7일 유효
    - 블랙리스트에 있는 토큰은 거부

    Args:
    - **refresh_token**: Refresh Token

    Returns:
    - 새로운 Access Token
    """
    # Refresh Token 블랙리스트 체크
    is_blacklisted = await redis_cache.is_token_blacklisted(
        token=request.refresh_token,
        token_type="refresh"
    )

    if is_blacklisted:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="이 Refresh Token은 무효화되었습니다. 다시 로그인하세요."
        )

    # Refresh Token으로 새 Access Token 생성
    new_access_token = refresh_access_token(request.refresh_token)

    if not new_access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh Token이 유효하지 않거나 만료되었습니다."
        )

    return RefreshTokenResponse(
        success=True,
        message="Access Token이 갱신되었습니다.",
        access_token=new_access_token
    )


@router.post("/logout", response_model=LogoutResponse)
async def logout(request: LogoutRequest):
    """
    로그아웃

    - Refresh Token을 블랙리스트에 추가 (Redis)
    - Access Token은 클라이언트에서 삭제 권장 (짧은 만료 시간)

    Args:
    - **refresh_token**: Refresh Token (선택)

    Returns:
    - 로그아웃 확인
    """
    # Refresh Token을 블랙리스트에 추가
    if request.refresh_token:
        try:
            # Refresh Token 블랙리스트 추가 (TTL: 7일)
            await redis_cache.add_token_to_blacklist(
                token=request.refresh_token,
                token_type="refresh",
                ttl=604800  # 7일 (Refresh Token 만료 시간)
            )
            logger.info("Refresh token added to blacklist")

            return LogoutResponse(
                success=True,
                message="로그아웃되었습니다. Refresh Token이 무효화되었습니다."
            )

        except Exception as e:
            logger.error(f"Failed to add token to blacklist: {str(e)}")
            # Redis 실패 시에도 로그아웃 성공으로 처리 (클라이언트 토큰 삭제 권장)
            return LogoutResponse(
                success=True,
                message="로그아웃되었습니다. 토큰을 삭제하세요."
            )
    else:
        # Refresh Token이 없으면 클라이언트에서 Access Token만 삭제
        return LogoutResponse(
            success=True,
            message="로그아웃되었습니다. 토큰을 삭제하세요."
        )


@router.get("/me")
async def get_current_user(
    db: AsyncSession = Depends(get_db),
    current_user_id: str = Depends(get_user_id)
):
    """
    현재 로그인한 사용자 정보 조회

    Returns:
    - 사용자 정보 (비밀번호 제외)
    """
    user = await get_user_by_id(db, current_user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자를 찾을 수 없습니다."
        )

    return {
        "user_id": user.id,
        "email": user.email,
        "name": user.name,
        "is_2fa_enabled": user.is_2fa_enabled,
        "is_active": user.is_active,
        "created_at": user.created_at.isoformat() if user.created_at else None
    }
