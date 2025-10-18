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
from app.services.binance_client import BinanceClient
from app.services.okx_client import OKXClient

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

        # API 키 유효성 검증
        logger.info(f"Validating API credentials for {exchange_lower}")

        try:
            if exchange_lower == "binance":
                # Binance API 키 검증
                client = BinanceClient(
                    api_key=account.api_key,
                    api_secret=account.api_secret,
                    testnet=account.testnet
                )
                validation_result = client.validate_credentials()

            elif exchange_lower == "okx":
                # OKX API 키 검증
                client = OKXClient(
                    api_key=account.api_key,
                    api_secret=account.api_secret,
                    passphrase=account.passphrase,
                    testnet=account.testnet
                )
                validation_result = client.validate_credentials()

            # 검증 실패 시
            if not validation_result.get("valid", False):
                error_message = validation_result.get("message", "Invalid API credentials")
                logger.warning(f"API validation failed: {error_message}")
                raise HTTPException(
                    status_code=400,
                    detail=f"API key validation failed: {error_message}"
                )

            # 검증 성공 로그
            logger.info(
                f"API credentials validated successfully for {exchange_lower}. "
                f"Balance: {validation_result.get('details', {}).get('available_balance', 'N/A')} USDT"
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"API validation error: {str(e)}")
            raise HTTPException(
                status_code=400,
                detail=f"Failed to validate API credentials: {str(e)}"
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


@router.put("/{account_id}")
async def update_exchange_account(
    request: Request,
    account_id: str,
    account: ExchangeAccountCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    _: None = Depends(csrf_protect)
):
    """
    거래소 API 키 수정

    **보안:**
    - 사용자 인증 필수
    - CSRF 토큰 검증 필수
    - 사용자 본인의 계정만 수정 가능
    - 새로운 API 키 유효성 검증
    - AES-256 암호화 저장

    **참고:**
    - 거래소 종류는 변경할 수 없습니다
    - API 키, Secret, Passphrase를 모두 제공해야 합니다
    """
    try:
        logger.info(f"User {current_user.email} updating account {account_id}")

        # 기존 계정 조회
        api_key_record = db.query(ApiKey).filter(
            ApiKey.id == account_id,
            ApiKey.user_id == current_user.id
        ).first()

        if not api_key_record:
            raise HTTPException(status_code=404, detail="Account not found")

        # 거래소 종류 변경 불가
        exchange_lower = account.exchange.lower()
        if api_key_record.exchange != exchange_lower:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot change exchange type. Current: {api_key_record.exchange}, Requested: {exchange_lower}"
            )

        # 거래소 검증
        if exchange_lower not in ["binance", "okx"]:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported exchange: {account.exchange}"
            )

        # OKX는 passphrase 필수
        if exchange_lower == "okx" and not account.passphrase:
            raise HTTPException(
                status_code=400,
                detail="Passphrase is required for OKX exchange"
            )

        # 새로운 API 키 유효성 검증
        logger.info(f"Validating new API credentials for {exchange_lower}")

        try:
            if exchange_lower == "binance":
                client = BinanceClient(
                    api_key=account.api_key,
                    api_secret=account.api_secret,
                    testnet=account.testnet
                )
                validation_result = client.validate_credentials()

            elif exchange_lower == "okx":
                client = OKXClient(
                    api_key=account.api_key,
                    api_secret=account.api_secret,
                    passphrase=account.passphrase,
                    testnet=account.testnet
                )
                validation_result = client.validate_credentials()

            if not validation_result.get("valid", False):
                error_message = validation_result.get("message", "Invalid API credentials")
                logger.warning(f"API validation failed: {error_message}")
                raise HTTPException(
                    status_code=400,
                    detail=f"New API key validation failed: {error_message}"
                )

            logger.info(f"New API credentials validated successfully")

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"API validation error: {str(e)}")
            raise HTTPException(
                status_code=400,
                detail=f"Failed to validate new API credentials: {str(e)}"
            )

        # 새로운 API 키 암호화
        encrypted = crypto_service.encrypt_api_credentials(
            api_key=account.api_key,
            api_secret=account.api_secret,
            passphrase=account.passphrase
        )

        # 데이터베이스 업데이트
        api_key_record.api_key = encrypted["api_key"]
        api_key_record.api_secret = encrypted["api_secret"]
        api_key_record.passphrase = encrypted.get("passphrase")
        api_key_record.testnet = account.testnet

        db.commit()
        db.refresh(api_key_record)

        # OrderExecutor 업데이트
        executor_account_id = f"{current_user.id}_{account_id}"

        # 기존 클라이언트 삭제
        if exchange_lower == "binance":
            if executor_account_id in order_executor.binance_clients:
                del order_executor.binance_clients[executor_account_id]
            # 새로운 클라이언트 등록
            order_executor.register_binance_account(
                account_id=executor_account_id,
                api_key=account.api_key,
                api_secret=account.api_secret,
                testnet=account.testnet
            )
        elif exchange_lower == "okx":
            if executor_account_id in order_executor.okx_clients:
                del order_executor.okx_clients[executor_account_id]
            # 새로운 클라이언트 등록
            order_executor.register_okx_account(
                account_id=executor_account_id,
                api_key=account.api_key,
                api_secret=account.api_secret,
                passphrase=account.passphrase,
                testnet=account.testnet
            )

        logger.info(f"Account {account_id} updated successfully")

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
        logger.error(f"Failed to update account: {str(e)}", exc_info=True)
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


@router.get("/{account_id}/balance")
async def get_account_balance(
    account_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    계정 잔액 실시간 조회

    **보안:**
    - 사용자 인증 필수
    - 사용자 본인의 계정만 조회 가능

    **응답:**
    - asset: 자산 종류 (USDT)
    - available_balance: 사용 가능 잔액
    - total_balance: 총 잔액
    - testnet: 테스트넷 여부
    """
    try:
        # 계정 조회
        api_key_record = db.query(ApiKey).filter(
            ApiKey.id == account_id,
            ApiKey.user_id == current_user.id
        ).first()

        if not api_key_record:
            raise HTTPException(status_code=404, detail="Account not found")

        # API 키 복호화
        decrypted = crypto_service.decrypt_api_credentials({
            "api_key": api_key_record.api_key,
            "api_secret": api_key_record.api_secret,
            "passphrase": api_key_record.passphrase
        })

        # 거래소 클라이언트 생성 및 잔액 조회
        if api_key_record.exchange == "binance":
            client = BinanceClient(
                api_key=decrypted["api_key"],
                api_secret=decrypted["api_secret"],
                testnet=api_key_record.testnet
            )
        elif api_key_record.exchange == "okx":
            client = OKXClient(
                api_key=decrypted["api_key"],
                api_secret=decrypted["api_secret"],
                passphrase=decrypted["passphrase"],
                testnet=api_key_record.testnet
            )
        else:
            raise HTTPException(status_code=400, detail="Unsupported exchange")

        # 잔액 조회
        balance = client.get_account_balance()

        return {
            "account_id": account_id,
            "exchange": api_key_record.exchange,
            "testnet": api_key_record.testnet,
            **balance
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get balance: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{account_id}/positions")
async def get_account_positions(
    account_id: str,
    symbol: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    계정 포지션 실시간 조회

    **보안:**
    - 사용자 인증 필수
    - 사용자 본인의 계정만 조회 가능

    **파라미터:**
    - symbol: 특정 심볼만 조회 (선택사항)

    **응답:**
    - positions: 활성 포지션 목록
    - total_count: 포지션 개수
    """
    try:
        # 계정 조회
        api_key_record = db.query(ApiKey).filter(
            ApiKey.id == account_id,
            ApiKey.user_id == current_user.id
        ).first()

        if not api_key_record:
            raise HTTPException(status_code=404, detail="Account not found")

        # API 키 복호화
        decrypted = crypto_service.decrypt_api_credentials({
            "api_key": api_key_record.api_key,
            "api_secret": api_key_record.api_secret,
            "passphrase": api_key_record.passphrase
        })

        # 거래소 클라이언트 생성 및 포지션 조회
        if api_key_record.exchange == "binance":
            client = BinanceClient(
                api_key=decrypted["api_key"],
                api_secret=decrypted["api_secret"],
                testnet=api_key_record.testnet
            )
        elif api_key_record.exchange == "okx":
            client = OKXClient(
                api_key=decrypted["api_key"],
                api_secret=decrypted["api_secret"],
                passphrase=decrypted["passphrase"],
                testnet=api_key_record.testnet
            )
        else:
            raise HTTPException(status_code=400, detail="Unsupported exchange")

        # 포지션 조회
        positions = client.get_positions(symbol=symbol)

        return {
            "account_id": account_id,
            "exchange": api_key_record.exchange,
            "testnet": api_key_record.testnet,
            "positions": positions,
            "total_count": len(positions)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get positions: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
