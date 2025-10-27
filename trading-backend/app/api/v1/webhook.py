"""
TradingView Webhook API with Trading Config Integration

Features:
- TradingView 알림 수신
- Trading Config 기반 자동 주문 크기 계산
- 시그널 검증 및 실행
- 보안 검증 (Secret Key)
- 실시간 주문 전송
"""

from fastapi import APIRouter, HTTPException, Request, Depends
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging
import hmac
from datetime import datetime

from app.services.order_executor import order_executor, Exchange
from app.core.config import settings
from app.core.symbols import symbol_config
from app.database.session import get_db
from app.models.trading_config import TradingConfig
from app.models.api_key import ApiKey

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhook", tags=["webhook"])

# 보안 상수
VALID_ACTIONS = {"long", "short", "close_long", "close_short", "close_all"}
VALID_EXCHANGES = {"binance", "okx"}
MAX_LEVERAGE = 125
MIN_LEVERAGE = 1


class TradingViewWebhook(BaseModel):
    """TradingView 웹훅 페이로드 (Trading Config 통합)"""
    account_id: str = Field(..., description="API Key ID (Trading Config의 api_key_id)", min_length=1, max_length=100)
    exchange: str = Field(..., description="거래소 (binance or okx)", min_length=3, max_length=20)
    action: str = Field(..., description="액션 (long, short, close_long, close_short, close_all)", min_length=3, max_length=20)
    symbol: str = Field(..., description="심볼 (BTCUSDT)", min_length=6, max_length=15)
    price: Optional[float] = Field(None, description="현재 가격 (선택사항)", gt=0)
    secret: str = Field(..., description="웹훅 검증 키", min_length=32, max_length=128)
    timestamp: Optional[int] = Field(None, description="요청 타임스탬프 (초 단위)")

    # Trading Config로부터 자동 계산되므로 선택사항
    quantity: Optional[float] = Field(None, description="수량 (Trading Config에서 자동 계산)", gt=0)
    leverage: Optional[int] = Field(None, description="레버리지 (Trading Config에서 자동 적용)", ge=MIN_LEVERAGE, le=MAX_LEVERAGE)
    stop_loss: Optional[float] = Field(None, description="손절가 (Trading Config에서 자동 계산)", gt=0)
    take_profit: Optional[float] = Field(None, description="익절가 (Trading Config에서 자동 계산)", gt=0)

    @validator('exchange')
    def validate_exchange(cls, v):
        if v.lower() not in VALID_EXCHANGES:
            raise ValueError(f"Invalid exchange. Must be one of: {', '.join(VALID_EXCHANGES)}")
        return v.lower()

    @validator('action')
    def validate_action(cls, v):
        if v.lower() not in VALID_ACTIONS:
            raise ValueError(f"Invalid action. Must be one of: {', '.join(VALID_ACTIONS)}")
        return v.lower()

    @validator('symbol')
    def validate_symbol(cls, v, values):
        symbol_upper = v.upper()
        exchange = values.get('exchange', 'binance').lower()

        if not symbol_config.validate_symbol(symbol_upper, exchange):
            supported = ", ".join([
                symbol_config.get_binance_symbol(s) if exchange == 'binance'
                else symbol_config.get_okx_symbol(s)
                for s in symbol_config.SUPPORTED_SYMBOLS
            ])
            raise ValueError(
                f"Unsupported symbol: {symbol_upper}. "
                f"Supported symbols for {exchange}: {supported}"
            )

        return symbol_upper

    @validator('timestamp')
    def validate_timestamp(cls, v):
        if v is None:
            return v

        current_time = datetime.utcnow().timestamp()
        time_diff = abs(current_time - v)

        if time_diff > 300:  # 5분 = 300초
            raise ValueError(f"Request timestamp too old or too far in future (diff: {time_diff:.0f}s)")

        return v


class WebhookResponse(BaseModel):
    """웹훅 응답"""
    success: bool
    message: str
    order_details: Optional[Dict[str, Any]] = None
    trading_config_applied: Optional[Dict[str, Any]] = None


def verify_webhook_secret(payload_secret: str, expected_secret: str) -> bool:
    """웹훅 Secret 검증"""
    return hmac.compare_digest(payload_secret, expected_secret)


async def get_trading_config(
    api_key_id: str,
    db: AsyncSession
) -> Optional[TradingConfig]:
    """
    API Key ID로 활성화된 Trading Config 조회

    Returns:
        TradingConfig 인스턴스 또는 None
    """
    stmt = select(TradingConfig).where(
        TradingConfig.api_key_id == api_key_id,
        TradingConfig.is_active == True
    ).order_by(TradingConfig.created_at.desc())

    result = await db.execute(stmt)
    config = result.scalar_one_or_none()

    return config


async def calculate_order_quantity(
    config: TradingConfig,
    account_id: str,
    exchange: Exchange,
    symbol: str,
    action: str
) -> float:
    """
    Trading Config 기반 주문 수량 계산

    Args:
        config: TradingConfig 인스턴스
        account_id: API Key ID
        exchange: 거래소
        symbol: 심볼
        action: 액션

    Returns:
        계산된 주문 수량 (USDT)
    """
    try:
        # Close 액션은 수량 계산 불필요
        if action in ["close_long", "close_short", "close_all"]:
            return 0.0

        # 계좌 잔고 조회
        if exchange == Exchange.BINANCE:
            client = order_executor.binance_clients.get(account_id)
        else:
            client = order_executor.okx_clients.get(account_id)

        if not client:
            raise ValueError(f"Exchange client not found for account {account_id}")

        balance_data = client.get_account_balance()

        # Binance: availableBalance, OKX: availBal
        available_balance = 0.0
        if exchange == Exchange.BINANCE:
            for asset in balance_data.get('assets', []):
                if asset.get('asset') == 'USDT':
                    available_balance = float(asset.get('availableBalance', 0))
                    break
        else:  # OKX
            for detail in balance_data.get('data', []):
                for balance in detail.get('details', []):
                    if balance.get('ccy') == 'USDT':
                        available_balance = float(balance.get('availBal', 0))
                        break

        if available_balance <= 0:
            raise ValueError(f"Insufficient balance: {available_balance} USDT")

        # Investment Type에 따라 수량 계산
        if config.investment_type.value == "percentage":
            # 비율 기반: investment_value는 0.0 ~ 1.0 (예: 0.1 = 10%)
            order_amount = available_balance * config.investment_value
        else:  # fixed
            # 고정 금액: investment_value는 USDT 금액 (예: 100 = 100 USDT)
            order_amount = config.investment_value

        # 최소 주문 금액 검증 (Binance 최소 5 USDT, OKX 최소 1 USDT)
        min_order = 5.0 if exchange == Exchange.BINANCE else 1.0
        if order_amount < min_order:
            raise ValueError(
                f"Order amount too small: {order_amount:.2f} USDT "
                f"(minimum: {min_order} USDT)"
            )

        logger.info(
            f"Calculated order quantity: {order_amount:.2f} USDT "
            f"(available: {available_balance:.2f}, "
            f"type: {config.investment_type.value}, "
            f"value: {config.investment_value})"
        )

        return order_amount

    except Exception as e:
        logger.error(f"Failed to calculate order quantity: {str(e)}", exc_info=True)
        raise


@router.post("/tradingview", response_model=WebhookResponse)
async def receive_tradingview_webhook(
    webhook: TradingViewWebhook,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    TradingView 웹훅 수신 및 Trading Config 기반 주문 실행

    Trading Config 통합 기능:
    - API Key에 연결된 Trading Config 자동 조회
    - investment_type (percentage/fixed)에 따른 주문 크기 자동 계산
    - leverage, stop_loss_percentage, take_profit_percentage 자동 적용

    **Pine Script 알림 설정 (간소화):**
    ```
    alert(
        '{"account_id":"YOUR_API_KEY_ID", "exchange":"binance", "action":"long", "symbol":"BTCUSDT", "secret":"YOUR_SECRET"}',
        alert.freq_once_per_bar_close
    )
    ```

    주의: account_id는 Settings 페이지에서 확인한 API Key ID 사용
    """
    try:
        logger.info(
            f"Webhook received: account={webhook.account_id}, "
            f"exchange={webhook.exchange}, action={webhook.action}, symbol={webhook.symbol}"
        )

        # 1. Secret 검증
        if not verify_webhook_secret(webhook.secret, settings.WEBHOOK_SECRET):
            logger.warning(f"Invalid webhook secret from {request.client.host}")
            raise HTTPException(status_code=401, detail="Invalid webhook secret")

        # 2. Exchange 검증
        try:
            exchange = Exchange(webhook.exchange.lower())
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid exchange: {webhook.exchange}. Must be 'binance' or 'okx'"
            )

        # 3. Trading Config 조회
        trading_config = await get_trading_config(webhook.account_id, db)

        if not trading_config:
            logger.warning(f"No active Trading Config found for account {webhook.account_id}")
            # Trading Config 없으면 기본값 사용
            config_leverage = webhook.leverage or 10
            config_stop_loss = None
            config_take_profit = None
            config_quantity = webhook.quantity
            config_applied = None
        else:
            # Trading Config 설정값 적용
            config_leverage = webhook.leverage or trading_config.leverage
            config_stop_loss = trading_config.stop_loss_percentage
            config_take_profit = trading_config.take_profit_percentage

            # 주문 수량 자동 계산 (quantity 미지정 시)
            if webhook.quantity is None and webhook.action not in ["close_long", "close_short", "close_all"]:
                config_quantity = await calculate_order_quantity(
                    trading_config,
                    webhook.account_id,
                    exchange,
                    webhook.symbol,
                    webhook.action
                )
            else:
                config_quantity = webhook.quantity

            config_applied = {
                "config_id": trading_config.id,
                "strategy": trading_config.strategy,
                "investment_type": trading_config.investment_type.value,
                "investment_value": trading_config.investment_value,
                "leverage": config_leverage,
                "stop_loss_percentage": config_stop_loss,
                "take_profit_percentage": config_take_profit,
                "calculated_quantity_usdt": config_quantity
            }

            logger.info(f"Trading Config applied: {config_applied}")

        # 4. 시그널 구성
        signal = {
            "action": webhook.action.lower(),
            "symbol": webhook.symbol.upper(),
            "price": webhook.price,
            "quantity": config_quantity,
            "leverage": config_leverage,
            "stop_loss": webhook.stop_loss,  # ATR 기반 자동 계산은 OrderExecutor에서 처리
            "take_profit": webhook.take_profit,
            "stop_loss_percentage": config_stop_loss,
            "take_profit_percentage": config_take_profit
        }

        # 5. 주문 실행
        result = order_executor.execute_signal(
            account_id=webhook.account_id,
            exchange=exchange,
            signal=signal
        )

        logger.info(f"Order executed successfully: {result}")

        return WebhookResponse(
            success=True,
            message=f"{webhook.action.upper()} order executed on {webhook.exchange}",
            order_details=result,
            trading_config_applied=config_applied
        )

    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        logger.error(f"Webhook execution failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Order execution failed: {str(e)}")


@router.get("/health")
async def webhook_health():
    """웹훅 서비스 헬스체크"""
    return {
        "status": "healthy",
        "service": "TradingView Webhook Receiver (Trading Config Integrated)",
        "registered_accounts": {
            "binance": len(order_executor.binance_clients),
            "okx": len(order_executor.okx_clients)
        }
    }


@router.get("/test-config/{account_id}")
async def test_trading_config(
    account_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Trading Config 테스트 (개발용)

    특정 API Key ID의 활성화된 Trading Config 조회
    """
    config = await get_trading_config(account_id, db)

    if not config:
        raise HTTPException(
            status_code=404,
            detail=f"No active Trading Config found for account {account_id}"
        )

    return {
        "config_id": config.id,
        "api_key_id": config.api_key_id,
        "strategy": config.strategy,
        "investment_type": config.investment_type.value,
        "investment_value": config.investment_value,
        "leverage": config.leverage,
        "stop_loss_percentage": config.stop_loss_percentage,
        "take_profit_percentage": config.take_profit_percentage,
        "is_active": config.is_active,
        "created_at": str(config.created_at)
    }


# ============================================
# Webhook CRUD Endpoints
# ============================================

from typing import List
from app.core.auth import get_current_user
from app.models.user import User


class WebhookCreate(BaseModel):
    """Webhook 생성 요청"""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    is_active: bool = Field(default=True)


class WebhookUpdate(BaseModel):
    """Webhook 수정 요청"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    is_active: Optional[bool] = None


class WebhookListResponse(BaseModel):
    """Webhook 목록 응답"""
    id: str
    name: str
    description: Optional[str]
    webhook_url: str
    secret_token: str
    is_active: bool
    total_triggers: int
    last_triggered: Optional[str]
    created_at: str


@router.get("", response_model=List[WebhookListResponse])
async def list_webhooks(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """사용자의 Webhook 목록 조회"""
    try:
        from app.models.webhook import Webhook
        
        stmt = select(Webhook).where(
            Webhook.user_id == current_user.id
        ).order_by(Webhook.created_at.desc())
        
        result = await db.execute(stmt)
        webhooks = result.scalars().all()
        
        return [
            WebhookListResponse(
                id=w.id,
                name=w.name,
                description=w.description,
                webhook_url=w.webhook_url,
                secret_token=w.secret_token,
                is_active=w.is_active,
                total_triggers=w.total_triggers,
                last_triggered=w.last_triggered.isoformat() if w.last_triggered else None,
                created_at=w.created_at.isoformat()
            )
            for w in webhooks
        ]
        
    except Exception as e:
        logger.error(f"Failed to list webhooks: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("", response_model=WebhookListResponse)
async def create_webhook(
    webhook_data: WebhookCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """새 Webhook 생성 - webhook_url과 secret_token이 자동 생성됩니다"""
    try:
        from app.models.webhook import Webhook
        import secrets
        from uuid import uuid4
        
        # Generate unique ID and secret
        webhook_id = str(uuid4())
        secret_token = secrets.token_urlsafe(32)
        
        # Generate webhook URL
        webhook_url = f"{settings.BACKEND_URL or http://localhost:8001}/api/v1/webhook/tradingview"
        
        # Create webhook
        new_webhook = Webhook(
            id=webhook_id,
            user_id=current_user.id,
            name=webhook_data.name,
            description=webhook_data.description,
            webhook_url=webhook_url,
            secret_token=secret_token,
            is_active=webhook_data.is_active,
            total_triggers=0
        )
        
        db.add(new_webhook)
        await db.commit()
        await db.refresh(new_webhook)
        
        logger.info(f"Webhook created: {webhook_id} for user {current_user.id}")
        
        return WebhookListResponse(
            id=new_webhook.id,
            name=new_webhook.name,
            description=new_webhook.description,
            webhook_url=new_webhook.webhook_url,
            secret_token=new_webhook.secret_token,
            is_active=new_webhook.is_active,
            total_triggers=new_webhook.total_triggers,
            last_triggered=new_webhook.last_triggered.isoformat() if new_webhook.last_triggered else None,
            created_at=new_webhook.created_at.isoformat()
        )
        
    except Exception as e:
        logger.error(f"Failed to create webhook: {str(e)}", exc_info=True)
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{webhook_id}")
async def delete_webhook(
    webhook_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Webhook 삭제"""
    try:
        from app.models.webhook import Webhook
        
        stmt = select(Webhook).where(
            Webhook.id == webhook_id,
            Webhook.user_id == current_user.id
        )
        
        result = await db.execute(stmt)
        webhook = result.scalar_one_or_none()
        
        if not webhook:
            raise HTTPException(status_code=404, detail="Webhook not found")
        
        await db.delete(webhook)
        await db.commit()
        
        logger.info(f"Webhook deleted: {webhook_id}")
        
        return {"success": True, "message": "Webhook deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete webhook: {str(e)}", exc_info=True)
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
