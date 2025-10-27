from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging

from app.core.auth import get_current_user
from app.database.session import get_db
from app.models.user import User
from app.models.api_key import ApiKey
from app.core.crypto import crypto_service
from app.services.binance_client import BinanceClient
from app.services.okx_client import OKXClient

router = APIRouter()
logger = logging.getLogger(__name__)


class WalletTransferRequest(BaseModel):
    account_id: str = Field(..., description="API Key ID from accounts-secure/list")
    from_account: str = Field(..., description="Source account: SPOT, FUTURES (Binance) or FUNDING, TRADING (OKX)")
    to_account: str = Field(..., description="Destination account")
    asset: str = Field(default="USDT", description="Asset symbol (default: USDT)")
    amount: float = Field(..., gt=0, description="Transfer amount (must be positive)")


class WalletTransferResponse(BaseModel):
    success: bool
    message: str
    transfer_id: str
    exchange: str
    from_account: str
    to_account: str
    asset: str
    amount: float
    timestamp: int


@router.post("/transfer", response_model=WalletTransferResponse)
async def transfer_wallet_asset(
    request: WalletTransferRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    계정 간 자산 이동 API

    **지원 거래소:**
    - Binance: SPOT <-> FUTURES
    - OKX: FUNDING <-> TRADING
    """
    try:
        # 1. API 키 조회
        stmt = select(ApiKey).where(
            ApiKey.id == request.account_id,
            ApiKey.user_id == current_user.id,
            ApiKey.is_active == True
        )
        result = await db.execute(stmt)
        api_key = result.scalar_one_or_none()

        if not api_key:
            raise HTTPException(status_code=404, detail="API key not found or inactive")

        # 2. API 키 복호화
        decrypted = crypto_service.decrypt_api_credentials({
            "api_key": api_key.api_key,
            "api_secret": api_key.api_secret,
            "passphrase": api_key.passphrase
        })

        # 3. 거래소별 처리
        exchange = api_key.exchange.lower()

        if exchange == "binance":
            client = BinanceClient(
                api_key=decrypted["api_key"],
                api_secret=decrypted["api_secret"],
                testnet=api_key.testnet
            )

            valid_accounts = ["SPOT", "FUTURES"]
            if request.from_account.upper() not in valid_accounts or request.to_account.upper() not in valid_accounts:
                raise HTTPException(status_code=400, detail=f"Invalid Binance account type. Use: {', '.join(valid_accounts)}")

            if request.from_account.upper() == request.to_account.upper():
                raise HTTPException(status_code=400, detail="Source and destination cannot be the same")

            result = client.transfer_asset(
                from_account=request.from_account.upper(),
                to_account=request.to_account.upper(),
                asset=request.asset.upper(),
                amount=request.amount
            )

            return WalletTransferResponse(
                success=True,
                message=f"Transferred {request.amount} {request.asset} from {request.from_account} to {request.to_account}",
                transfer_id=str(result["tranId"]),
                exchange="binance",
                from_account=request.from_account.upper(),
                to_account=request.to_account.upper(),
                asset=request.asset.upper(),
                amount=request.amount,
                timestamp=result["timestamp"]
            )

        elif exchange == "okx":
            client = OKXClient(
                api_key=decrypted["api_key"],
                api_secret=decrypted["api_secret"],
                passphrase=decrypted["passphrase"],
                testnet=api_key.testnet
            )

            account_mapping = {
                "FUNDING": "6",
                "TRADING": "18"
            }

            from_acc = request.from_account.upper()
            to_acc = request.to_account.upper()

            if from_acc not in account_mapping or to_acc not in account_mapping:
                raise HTTPException(status_code=400, detail="Invalid OKX account type. Use: FUNDING, TRADING")

            if from_acc == to_acc:
                raise HTTPException(status_code=400, detail="Source and destination cannot be the same")

            result = client.transfer_asset(
                from_account=account_mapping[from_acc],
                to_account=account_mapping[to_acc],
                currency=request.asset.upper(),
                amount=request.amount
            )

            return WalletTransferResponse(
                success=True,
                message=f"Transferred {request.amount} {request.asset} from {from_acc} to {to_acc}",
                transfer_id=result["transfer_id"],
                exchange="okx",
                from_account=from_acc,
                to_account=to_acc,
                asset=request.asset.upper(),
                amount=request.amount,
                timestamp=int(result.get("timestamp", 0))
            )

        else:
            raise HTTPException(status_code=400, detail=f"Unsupported exchange: {exchange}")

    except ValueError as e:
        logger.warning(f"Transfer validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        logger.error(f"Transfer failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Transfer failed: {str(e)}")


@router.get("/balance-check/{account_id}")
async def check_balance_before_transfer(
    account_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    이동 전 계정 잔액 조회
    """
    try:
        stmt = select(ApiKey).where(
            ApiKey.id == account_id,
            ApiKey.user_id == current_user.id,
            ApiKey.is_active == True
        )
        result = await db.execute(stmt)
        api_key = result.scalar_one_or_none()

        if not api_key:
            raise HTTPException(status_code=404, detail="API key not found")

        decrypted = crypto_service.decrypt_api_credentials({
            "api_key": api_key.api_key,
            "api_secret": api_key.api_secret,
            "passphrase": api_key.passphrase
        })

        exchange = api_key.exchange.lower()

        if exchange == "binance":
            client = BinanceClient(
                api_key=decrypted["api_key"],
                api_secret=decrypted["api_secret"],
                testnet=api_key.testnet
            )
            balance = client.get_account_balance()

            return {
                "success": True,
                "exchange": "binance",
                "balances": {
                    "SPOT": {
                        "USDT": balance["account_structure"]["spot"]["usdt_available"]
                    },
                    "FUTURES": {
                        "USDT": balance["account_structure"]["futures"]["usdt_available"]
                    }
                }
            }

        elif exchange == "okx":
            client = OKXClient(
                api_key=decrypted["api_key"],
                api_secret=decrypted["api_secret"],
                passphrase=decrypted["passphrase"],
                testnet=api_key.testnet
            )
            balance = client.get_account_balance()

            return {
                "success": True,
                "exchange": "okx",
                "balances": {
                    "FUNDING": {
                        "USDT": balance["account_structure"]["funding"]["usdt_available"]
                    },
                    "TRADING": {
                        "USDT": balance["account_structure"]["trading"]["usdt_available"]
                    }
                }
            }

    except Exception as e:
        logger.error(f"Balance check failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
