"""
Exchange API Key Management with Rate Limiting
거래소 API 키 관리 (보안 강화 버전)
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import List
import logging

from app.database.session import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.models.api_key import ApiKey
from app.core.crypto import crypto_service
from app.core.rate_limit import limiter, RATE_LIMITS
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/accounts-secure", tags=["Secure Accounts"])


# === Pydantic Models ===

class RegisterAccountRequest(BaseModel):
    exchange: str  # "binance" or "okx"
    api_key: str
    api_secret: str
    passphrase: str | None = None  # OKX only
    testnet: bool = True


class AccountResponse(BaseModel):
    id: str
    exchange: str
    testnet: bool
    is_active: bool
    created_at: str

    class Config:
        from_attributes = True


class AccountListResponse(BaseModel):
    accounts: List[AccountResponse]
    total: int


# === Endpoints ===

@router.post("/register", response_model=AccountResponse)
@limiter.limit(RATE_LIMITS["accounts_register"])
async def register_exchange_account(
    request: Request,  # Rate limiting 필요
    data: RegisterAccountRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    거래소 API 키 등록 (AES-256 암호화)

    **Rate Limit**: 10회/시간

    **보안**:
    - API 키는 AES-256으로 암호화 후 저장
    - 평문으로 데이터베이스에 저장되지 않음
    """
    logger.info(f"User {current_user.id} registering {data.exchange} account")

    # Validation
    if data.exchange not in ["binance", "okx"]:
        raise HTTPException(400, "Unsupported exchange")

    if data.exchange == "okx" and not data.passphrase:
        raise HTTPException(400, "Passphrase is required for OKX")

    # 암호화
    encrypted = crypto_service.encrypt_api_credentials(
        api_key=data.api_key,
        api_secret=data.api_secret,
        passphrase=data.passphrase
    )

    # DB 저장
    api_key_obj = ApiKey(
        user_id=current_user.id,
        exchange=data.exchange,
        api_key=encrypted["api_key"],
        api_secret=encrypted["api_secret"],
        passphrase=encrypted.get("passphrase"),
        testnet=data.testnet,
        is_active=True
    )

    db.add(api_key_obj)
    db.commit()
    db.refresh(api_key_obj)

    logger.info(f"Account registered: {api_key_obj.id}")

    return AccountResponse(
        id=api_key_obj.id,
        exchange=api_key_obj.exchange,
        testnet=api_key_obj.testnet,
        is_active=api_key_obj.is_active,
        created_at=api_key_obj.created_at.isoformat()
    )


@router.get("/list", response_model=AccountListResponse)
@limiter.limit(RATE_LIMITS["accounts_list"])
async def list_exchange_accounts(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    사용자의 모든 거래소 계정 조회

    **Rate Limit**: 60회/시간

    **주의**: API 키와 시크릿은 반환하지 않음 (보안)
    """
    accounts = db.query(ApiKey).filter(
        ApiKey.user_id == current_user.id
    ).all()

    return AccountListResponse(
        accounts=[
            AccountResponse(
                id=acc.id,
                exchange=acc.exchange,
                testnet=acc.testnet,
                is_active=acc.is_active,
                created_at=acc.created_at.isoformat()
            )
            for acc in accounts
        ],
        total=len(accounts)
    )


@router.delete("/{account_id}")
@limiter.limit(RATE_LIMITS["accounts_modify"])
async def delete_exchange_account(
    request: Request,
    account_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    거래소 계정 삭제

    **Rate Limit**: 30회/시간
    """
    account = db.query(ApiKey).filter(
        ApiKey.id == account_id,
        ApiKey.user_id == current_user.id
    ).first()

    if not account:
        raise HTTPException(404, "Account not found")

    db.delete(account)
    db.commit()

    logger.info(f"Account deleted: {account_id}")

    return {"success": True, "message": "Account deleted successfully"}


@router.post("/{account_id}/toggle")
@limiter.limit(RATE_LIMITS["accounts_modify"])
async def toggle_account_status(
    request: Request,
    account_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    계정 활성화/비활성화 토글

    **Rate Limit**: 30회/시간
    """
    account = db.query(ApiKey).filter(
        ApiKey.id == account_id,
        ApiKey.user_id == current_user.id
    ).first()

    if not account:
        raise HTTPException(404, "Account not found")

    # Toggle
    account.is_active = not account.is_active
    db.commit()

    logger.info(f"Account {account_id} toggled to: {account.is_active}")

    return {
        "success": True,
        "account_id": account_id,
        "is_active": account.is_active
    }


@router.get("/{account_id}/balance")
@limiter.limit(RATE_LIMITS["balance_check"])
async def get_account_balance(
    request: Request,
    account_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    거래소 계정 잔액 조회

    **Rate Limit**: 120회/시간
    """
    account = db.query(ApiKey).filter(
        ApiKey.id == account_id,
        ApiKey.user_id == current_user.id
    ).first()

    if not account:
        raise HTTPException(404, "Account not found")

    if not account.is_active:
        raise HTTPException(400, "Account is not active")

    # 복호화
    decrypted = crypto_service.decrypt_api_credentials({
        "api_key": account.api_key,
        "api_secret": account.api_secret,
        "passphrase": account.passphrase
    })

    # 거래소 API 호출
    if account.exchange == "binance":
        from app.services.binance_client import BinanceClient
        client = BinanceClient(
            api_key=decrypted["api_key"],
            api_secret=decrypted["api_secret"],
            testnet=account.testnet
        )
        return await client.get_account_balance()

    elif account.exchange == "okx":
        from app.services.okx_client import OKXClient
        client = OKXClient(
            api_key=decrypted["api_key"],
            api_secret=decrypted["api_secret"],
            passphrase=decrypted["passphrase"],
            testnet=account.testnet
        )
        return await client.get_account_balance()


@router.get("/{account_id}/positions")
@limiter.limit(RATE_LIMITS["positions_check"])
async def get_account_positions(
    request: Request,
    account_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    거래소 계정 포지션 조회

    **Rate Limit**: 120회/시간
    """
    account = db.query(ApiKey).filter(
        ApiKey.id == account_id,
        ApiKey.user_id == current_user.id
    ).first()

    if not account:
        raise HTTPException(404, "Account not found")

    if not account.is_active:
        raise HTTPException(400, "Account is not active")

    # 복호화
    decrypted = crypto_service.decrypt_api_credentials({
        "api_key": account.api_key,
        "api_secret": account.api_secret,
        "passphrase": account.passphrase
    })

    # 거래소 API 호출
    if account.exchange == "binance":
        from app.services.binance_client import BinanceClient
        client = BinanceClient(
            api_key=decrypted["api_key"],
            api_secret=decrypted["api_secret"],
            testnet=account.testnet
        )
        return await client.get_positions()

    elif account.exchange == "okx":
        from app.services.okx_client import OKXClient
        client = OKXClient(
            api_key=decrypted["api_key"],
            api_secret=decrypted["api_secret"],
            passphrase=decrypted["passphrase"],
            testnet=account.testnet
        )
        return await client.get_positions()
