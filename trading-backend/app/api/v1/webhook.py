"""
TradingView Webhook API

Features:
- TradingView 알림 수신
- 시그널 검증 및 실행
- 보안 검증 (Secret Key)
- 실시간 주문 전송
"""

from fastapi import APIRouter, HTTPException, Request, Header
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, validator
import logging
import hmac
import hashlib
import re
from datetime import datetime, timedelta

from app.services.order_executor import order_executor, Exchange
from app.core.config import settings
from app.services.telegram_service import telegram_service
from app.api.v1.telegram import get_telegram_chat_id

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhook", tags=["webhook"])

# 보안 상수
VALID_ACTIONS = {"long", "short", "close_long", "close_short", "close_all"}
VALID_EXCHANGES = {"binance", "okx"}
MAX_LEVERAGE = 125  # Binance max leverage
MIN_LEVERAGE = 1
SYMBOL_PATTERN = re.compile(r'^[A-Z0-9]{3,12}USDT$')  # 심볼 패턴 (예: BTCUSDT, ETHUSDT)


class TradingViewWebhook(BaseModel):
    """TradingView 웹훅 페이로드 (강화된 검증)"""
    account_id: str = Field(..., description="사용자 계정 ID", min_length=1, max_length=100)
    exchange: str = Field(..., description="거래소 (binance or okx)", min_length=3, max_length=20)
    action: str = Field(..., description="액션 (long, short, close_long, close_short, close_all)", min_length=3, max_length=20)
    symbol: str = Field(..., description="심볼 (BTCUSDT)", min_length=6, max_length=15)
    price: Optional[float] = Field(None, description="현재 가격", gt=0)
    quantity: Optional[float] = Field(None, description="수량 (미지정시 자동 계산)", gt=0)
    leverage: Optional[int] = Field(None, description="레버리지", ge=MIN_LEVERAGE, le=MAX_LEVERAGE)
    stop_loss: Optional[float] = Field(None, description="손절가", gt=0)
    take_profit: Optional[float] = Field(None, description="익절가", gt=0)
    secret: str = Field(..., description="웹훅 검증 키", min_length=32, max_length=128)
    timestamp: Optional[int] = Field(None, description="요청 타임스탬프 (초 단위, replay attack 방지)")

    @validator('exchange')
    def validate_exchange(cls, v):
        """거래소 검증"""
        if v.lower() not in VALID_EXCHANGES:
            raise ValueError(f"Invalid exchange. Must be one of: {', '.join(VALID_EXCHANGES)}")
        return v.lower()

    @validator('action')
    def validate_action(cls, v):
        """액션 검증"""
        if v.lower() not in VALID_ACTIONS:
            raise ValueError(f"Invalid action. Must be one of: {', '.join(VALID_ACTIONS)}")
        return v.lower()

    @validator('symbol')
    def validate_symbol(cls, v):
        """심볼 검증 (USDT 페어만 허용)"""
        symbol_upper = v.upper()
        if not SYMBOL_PATTERN.match(symbol_upper):
            raise ValueError(f"Invalid symbol format. Must be [COIN]USDT (e.g., BTCUSDT, ETHUSDT)")
        return symbol_upper

    @validator('timestamp')
    def validate_timestamp(cls, v):
        """타임스탬프 검증 (replay attack 방지, ±5분 허용)"""
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


def verify_webhook_secret(payload_secret: str, expected_secret: str) -> bool:
    """웹훅 Secret 검증"""
    return hmac.compare_digest(payload_secret, expected_secret)


@router.post("/tradingview", response_model=WebhookResponse)
async def receive_tradingview_webhook(
    webhook: TradingViewWebhook,
    request: Request
):
    """
    TradingView 웹훅 수신 및 주문 실행

    TradingView에서 알림 발생 시 이 엔드포인트로 POST 요청이 전송됩니다.

    **Pine Script 알림 설정:**
    ```
    alert(
        '{"account_id":"your_account", "exchange":"binance", "action":"long", "symbol":"BTCUSDT", "leverage":10, "secret":"your_secret"}',
        alert.freq_once_per_bar_close
    )
    ```

    **지원 액션:**
    - `long`: 롱 진입
    - `short`: 숏 진입
    - `close_long`: 롱 포지션 청산
    - `close_short`: 숏 포지션 청산
    - `close_all`: 모든 포지션 청산

    **자동 기능:**
    - 수량 미지정 시 계좌의 10% 자동 사용
    - Stop Loss/Take Profit 자동 설정
    """
    # 텔레그램 채팅 ID 조회
    telegram_chat_id = get_telegram_chat_id(webhook.account_id)

    try:
        logger.info(
            f"Webhook received: account={webhook.account_id}, "
            f"exchange={webhook.exchange}, action={webhook.action}, symbol={webhook.symbol}"
        )

        # 텔레그램 알림: Webhook 수신
        if telegram_chat_id:
            telegram_service.send_webhook_received_notification(
                chat_id=telegram_chat_id,
                exchange=webhook.exchange,
                action=webhook.action,
                symbol=webhook.symbol,
                success=True
            )

        # 1. Secret 검증 (환경변수에서 읽어옴)
        if not verify_webhook_secret(webhook.secret, settings.WEBHOOK_SECRET):
            logger.warning(f"Invalid webhook secret from {request.client.host}")

            # 텔레그램 알림: Secret 검증 실패
            if telegram_chat_id:
                telegram_service.send_error_notification(
                    chat_id=telegram_chat_id,
                    error_type="Webhook Secret 검증 실패",
                    error_message="Invalid webhook secret",
                    context={"ip": request.client.host}
                )

            raise HTTPException(status_code=401, detail="Invalid webhook secret")

        # 2. Exchange 검증
        try:
            exchange = Exchange(webhook.exchange.lower())
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid exchange: {webhook.exchange}. Must be 'binance' or 'okx'"
            )

        # 3. 시그널 구성
        signal = {
            "action": webhook.action.lower(),
            "symbol": webhook.symbol.upper(),
            "price": webhook.price,
            "quantity": webhook.quantity,
            "leverage": webhook.leverage,
            "stop_loss": webhook.stop_loss,
            "take_profit": webhook.take_profit
        }

        # 4. 주문 실행
        result = order_executor.execute_signal(
            account_id=webhook.account_id,
            exchange=exchange,
            signal=signal
        )

        logger.info(f"Order executed successfully: {result}")

        # 텔레그램 알림: 주문 실행 성공
        if telegram_chat_id:
            telegram_service.send_order_notification(
                chat_id=telegram_chat_id,
                exchange=webhook.exchange,
                action=webhook.action,
                symbol=webhook.symbol,
                price=webhook.price or result.get("price"),
                quantity=webhook.quantity or result.get("quantity"),
                leverage=webhook.leverage,
                order_id=result.get("orderId") or result.get("order_id")
            )

        return WebhookResponse(
            success=True,
            message=f"{webhook.action.upper()} order executed on {webhook.exchange}",
            order_details=result
        )

    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")

        # 텔레그램 알림: 검증 에러
        if telegram_chat_id:
            telegram_service.send_error_notification(
                chat_id=telegram_chat_id,
                error_type="입력 검증 실패",
                error_message=str(e),
                context={
                    "exchange": webhook.exchange,
                    "action": webhook.action,
                    "symbol": webhook.symbol
                }
            )

        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        logger.error(f"Webhook execution failed: {str(e)}", exc_info=True)

        # 텔레그램 알림: 주문 실행 실패
        if telegram_chat_id:
            telegram_service.send_error_notification(
                chat_id=telegram_chat_id,
                error_type="주문 실행 실패",
                error_message=str(e),
                context={
                    "exchange": webhook.exchange,
                    "action": webhook.action,
                    "symbol": webhook.symbol
                }
            )

        raise HTTPException(status_code=500, detail=f"Order execution failed: {str(e)}")


@router.get("/health")
async def webhook_health():
    """웹훅 서비스 헬스체크"""
    return {
        "status": "healthy",
        "service": "TradingView Webhook Receiver",
        "registered_accounts": {
            "binance": len(order_executor.binance_clients),
            "okx": len(order_executor.okx_clients)
        }
    }
