"""
사용자 계정 관리 API (보안 강화 버전)

Features:
- 사용자 인증 필수
- API 키 암호화 저장 (AES-256)
- 데이터베이스 영구 저장
- 사용자별 API 키 관리
- 안전한 조회 및 삭제
"""

from fastapi import APIRouter, HTTPException, Depends, Request, Response
from pydantic import BaseModel, Field
from typing import Optional, List
from sqlalchemy.orm import Session
import uuid
import logging

from app.core.auth import get_current_user
from app.core.crypto import crypto_service
from app.core.csrf import csrf_protect, generate_csrf_token, set_csrf_cookie
from app.database.base import get_db
from app.models.user import User
from app.models.api_key import ApiKey
from app.services.order_executor import order_executor, Exchange

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/accounts-secure", tags=["🔐 Secure Account Management"])


class ExchangeAccountCreate(BaseModel):
    """거래소 계정 등록 (보안)"""
    exchange: str = Field(..., description="거래소 (binance or okx)")
    api_key: str = Field(..., description="API Key")
    api_secret: str = Field(..., description="API Secret")
    passphrase: Optional[str] = Field(None, description="API Passphrase (OKX only)")
    testnet: bool = Field(True, description="테스트넷 사용 여부")


class ExchangeAccountResponse(BaseModel):
    """계정 응답"""
    id: str
    exchange: str
    testnet: bool
    is_active: bool
    created_at: str


class ExchangeAccountList(BaseModel):
    """계정 목록"""
    accounts: List[ExchangeAccountResponse]
    total: int


@router.get("/csrf-token")
async def get_csrf_token(response: Response):
    """
    CSRF 토큰 발급

    **사용법:**
    1. 이 엔드포인트를 호출하여 CSRF 토큰을 쿠키로 받음
    2. 응답 body의 token 값을 추출
    3. POST, PUT, DELETE 요청 시 X-CSRF-Token 헤더에 포함

    **응답:**
    - Set-Cookie: csrf_token=<token>
    - Body: {"token": "<token>"}
    """
    token = generate_csrf_token()
    set_csrf_cookie(response, token)

    return {
        "token": token,
        "header_name": "X-CSRF-Token",
        "message": "CSRF token generated. Include this token in X-CSRF-Token header for state-changing requests."
    }


@router.post("/register", response_model=ExchangeAccountResponse)
async def register_exchange_account(
    request: Request,
    account: ExchangeAccountCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    _: None = Depends(csrf_protect)
):
    """
    거래소 API 키 등록 (암호화 저장)

    **보안:**
    - 사용자 인증 필수
    - CSRF 토큰 검증 필수
    - API 키 AES-256 암호화
    - 데이터베이스 영구 저장
    - 사용자별 격리

    **지원 거래소:**
    - Binance Futures
    - OKX Futures
    """
    try:
        logger.info(f"User {current_user.email} registering {account.exchange} account")

        # 거래소 검증
        exchange_lower = account.exchange.lower()
        if exchange_lower not in ["binance", "okx"]:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported exchange: {account.exchange}. Must be 'binance' or 'okx'"
            )

        # OKX는 passphrase 필수
        if exchange_lower == "okx" and not account.passphrase:
            raise HTTPException(
                status_code=400,
                detail="Passphrase is required for OKX exchange"
            )

        # API 키 암호화
        encrypted = crypto_service.encrypt_api_credentials(
            api_key=account.api_key,
            api_secret=account.api_secret,
            passphrase=account.passphrase
        )

        # 데이터베이스에 저장
        api_key_record = ApiKey(
            id=str(uuid.uuid4()),
            user_id=current_user.id,
            exchange=exchange_lower,
            api_key=encrypted["api_key"],
            api_secret=encrypted["api_secret"],
            passphrase=encrypted.get("passphrase"),
            testnet=account.testnet,
            is_active=True
        )

        db.add(api_key_record)
        db.commit()
        db.refresh(api_key_record)

        # OrderExecutor에도 등록 (메모리)
        account_id = f"{current_user.id}_{api_key_record.id}"

        if exchange_lower == "binance":
            order_executor.register_binance_account(
                account_id=account_id,
                api_key=account.api_key,
                api_secret=account.api_secret,
                testnet=account.testnet
            )
        elif exchange_lower == "okx":
            order_executor.register_okx_account(
                account_id=account_id,
                api_key=account.api_key,
                api_secret=account.api_secret,
                passphrase=account.passphrase,
                testnet=account.testnet
            )

        logger.info(f"Exchange account registered successfully: {api_key_record.id}")

        return ExchangeAccountResponse(
            id=api_key_record.id,
            exchange=api_key_record.exchange,
            testnet=api_key_record.testnet,
            is_active=api_key_record.is_active,
            created_at=api_key_record.created_at.isoformat()
        )

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to register exchange account: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list", response_model=ExchangeAccountList)
async def list_exchange_accounts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    등록된 거래소 계정 목록 조회

    **보안:**
    - API 키/Secret은 표시되지 않음
    - 사용자 본인의 계정만 조회 가능
    """
    try:
        accounts = db.query(ApiKey).filter(
            ApiKey.user_id == current_user.id,
            ApiKey.is_active == True
        ).all()

        account_list = [
            ExchangeAccountResponse(
                id=acc.id,
                exchange=acc.exchange,
                testnet=acc.testnet,
                is_active=acc.is_active,
                created_at=acc.created_at.isoformat()
            )
            for acc in accounts
        ]

        return ExchangeAccountList(
            accounts=account_list,
            total=len(account_list)
        )

    except Exception as e:
        logger.error(f"Failed to list accounts: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{account_id}")
async def delete_exchange_account(
    request: Request,
    account_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    _: None = Depends(csrf_protect)
):
    """
    거래소 계정 삭제

    **보안:**
    - 사용자 인증 필수
    - CSRF 토큰 검증 필수
    - 사용자 본인의 계정만 삭제 가능
    - 데이터베이스 및 메모리에서 모두 삭제
    """
    try:
        # 계정 조회
        api_key_record = db.query(ApiKey).filter(
            ApiKey.id == account_id,
            ApiKey.user_id == current_user.id
        ).first()

        if not api_key_record:
            raise HTTPException(status_code=404, detail="Account not found")

        # OrderExecutor에서 삭제
        executor_account_id = f"{current_user.id}_{account_id}"

        if api_key_record.exchange == "binance":
            if executor_account_id in order_executor.binance_clients:
                del order_executor.binance_clients[executor_account_id]
        elif api_key_record.exchange == "okx":
            if executor_account_id in order_executor.okx_clients:
                del order_executor.okx_clients[executor_account_id]

        # 데이터베이스에서 삭제
        db.delete(api_key_record)
        db.commit()

        logger.info(f"Account deleted: {account_id}")

        return {
            "success": True,
            "message": f"Account {account_id} deleted successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to delete account: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{account_id}/toggle")
async def toggle_account_status(
    request: Request,
    account_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    _: None = Depends(csrf_protect)
):
    """
    계정 활성화/비활성화 토글

    **보안:**
    - 사용자 인증 필수
    - CSRF 토큰 검증 필수

    비활성화된 계정은 자동 주문에 사용되지 않습니다.
    """
    try:
        api_key_record = db.query(ApiKey).filter(
            ApiKey.id == account_id,
            ApiKey.user_id == current_user.id
        ).first()

        if not api_key_record:
            raise HTTPException(status_code=404, detail="Account not found")

        # 상태 토글
        api_key_record.is_active = not api_key_record.is_active
        db.commit()
        db.refresh(api_key_record)

        logger.info(f"Account {account_id} toggled to: {api_key_record.is_active}")

        return {
            "success": True,
            "account_id": account_id,
            "is_active": api_key_record.is_active
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to toggle account: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
