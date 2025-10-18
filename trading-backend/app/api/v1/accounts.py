"""
사용자 계정 관리 API

Features:
- Binance/OKX API 키 등록
- 계정 상태 조회
- API 키 삭제
- 보안 관리
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
import logging

from app.services.order_executor import order_executor, Exchange

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/accounts", tags=["accounts"])


class BinanceAccountCreate(BaseModel):
    """Binance 계정 등록"""
    account_id: str = Field(..., description="계정 고유 ID (사용자명 등)")
    api_key: str = Field(..., description="Binance API Key")
    api_secret: str = Field(..., description="Binance API Secret")
    testnet: bool = Field(True, description="테스트넷 사용 여부")


class OKXAccountCreate(BaseModel):
    """OKX 계정 등록"""
    account_id: str = Field(..., description="계정 고유 ID")
    api_key: str = Field(..., description="OKX API Key")
    api_secret: str = Field(..., description="OKX API Secret")
    passphrase: str = Field(..., description="OKX API Passphrase")
    testnet: bool = Field(True, description="테스트넷 사용 여부")


class AccountResponse(BaseModel):
    """계정 응답"""
    success: bool
    message: str
    account_id: str
    exchange: str


class AccountStatus(BaseModel):
    """계정 상태"""
    account_id: str
    exchange: str
    balance: Dict[str, Any]
    positions: List[Dict[str, Any]]
    open_orders: Optional[List[Dict[str, Any]]] = None


@router.post("/binance/register", response_model=AccountResponse)
async def register_binance_account(account: BinanceAccountCreate):
    """
    Binance 계정 등록

    **필수 정보:**
    - API Key: Binance Futures 거래 권한 필요
    - API Secret: HMAC 서명용
    - Testnet 여부

    **API 키 생성 방법:**
    1. Binance 로그인
    2. API Management 페이지 접속
    3. Create API 클릭
    4. "Enable Futures" 체크
    5. API Key/Secret 복사

    **테스트넷:**
    - https://testnet.binancefuture.com 에서 테스트 API 키 생성 가능
    """
    try:
        # Binance 계정 등록
        order_executor.register_binance_account(
            account_id=account.account_id,
            api_key=account.api_key,
            api_secret=account.api_secret,
            testnet=account.testnet
        )

        logger.info(f"Binance account registered: {account.account_id}")

        return AccountResponse(
            success=True,
            message="Binance account registered successfully",
            account_id=account.account_id,
            exchange="binance"
        )

    except Exception as e:
        logger.error(f"Failed to register Binance account: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/okx/register", response_model=AccountResponse)
async def register_okx_account(account: OKXAccountCreate):
    """
    OKX 계정 등록

    **필수 정보:**
    - API Key
    - API Secret
    - API Passphrase (OKX 전용)

    **API 키 생성 방법:**
    1. OKX 로그인
    2. Profile → API 클릭
    3. Create V5 API Key
    4. Trade 권한 부여
    5. API Key/Secret/Passphrase 복사

    **주의사항:**
    - OKX는 Passphrase가 반드시 필요합니다
    - Passphrase는 분실 시 복구 불가능
    """
    try:
        # OKX 계정 등록
        order_executor.register_okx_account(
            account_id=account.account_id,
            api_key=account.api_key,
            api_secret=account.api_secret,
            passphrase=account.passphrase,
            testnet=account.testnet
        )

        logger.info(f"OKX account registered: {account.account_id}")

        return AccountResponse(
            success=True,
            message="OKX account registered successfully",
            account_id=account.account_id,
            exchange="okx"
        )

    except Exception as e:
        logger.error(f"Failed to register OKX account: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/status/{account_id}", response_model=AccountStatus)
async def get_account_status(
    account_id: str,
    exchange: str
):
    """
    계정 상태 조회

    **조회 정보:**
    - 잔액 (USDT)
    - 현재 포지션
    - 미체결 주문 (Binance만)
    - 레버리지 설정
    """
    try:
        exchange_enum = Exchange(exchange.lower())

        # 계정 상태 조회
        status = order_executor.get_account_status(
            account_id=account_id,
            exchange=exchange_enum
        )

        return AccountStatus(
            account_id=account_id,
            exchange=exchange,
            balance=status["balance"],
            positions=status["positions"],
            open_orders=status.get("open_orders")
        )

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid exchange: {exchange}. Must be 'binance' or 'okx'"
        )
    except Exception as e:
        logger.error(f"Failed to get account status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{account_id}")
async def delete_account(
    account_id: str,
    exchange: str
):
    """
    계정 삭제

    **주의:**
    - API 키 정보만 삭제됩니다
    - 거래소 계정 자체는 삭제되지 않습니다
    - 활성 포지션이 있는 경우 주의 필요
    """
    try:
        exchange_lower = exchange.lower()

        if exchange_lower == "binance":
            if account_id in order_executor.binance_clients:
                del order_executor.binance_clients[account_id]
                logger.info(f"Binance account deleted: {account_id}")
                return {
                    "success": True,
                    "message": f"Binance account {account_id} deleted"
                }
            else:
                raise HTTPException(status_code=404, detail="Account not found")

        elif exchange_lower == "okx":
            if account_id in order_executor.okx_clients:
                del order_executor.okx_clients[account_id]
                logger.info(f"OKX account deleted: {account_id}")
                return {
                    "success": True,
                    "message": f"OKX account {account_id} deleted"
                }
            else:
                raise HTTPException(status_code=404, detail="Account not found")

        else:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid exchange: {exchange}"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete account: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list")
async def list_accounts():
    """
    등록된 계정 목록 조회

    **반환 정보:**
    - Binance 계정 목록
    - OKX 계정 목록
    - API 키는 보안상 표시되지 않습니다
    """
    return {
        "binance_accounts": list(order_executor.binance_clients.keys()),
        "okx_accounts": list(order_executor.okx_clients.keys()),
        "total_accounts": (
            len(order_executor.binance_clients) +
            len(order_executor.okx_clients)
        )
    }
