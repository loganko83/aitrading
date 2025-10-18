"""
Telegram Notification API

Features:
- 텔레그램 채팅 ID 등록
- 알림 설정 관리
- 테스트 알림 전송
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict
import logging

from app.services.telegram_service import telegram_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/telegram", tags=["telegram"])

# 메모리 기반 chat_id 저장 (추후 DB로 확장 가능)
# account_id -> telegram_chat_id 매핑
user_telegram_settings: Dict[str, str] = {}


class TelegramRegister(BaseModel):
    """텔레그램 채팅 ID 등록"""
    account_id: str = Field(..., description="사용자 계정 ID (거래소 계정 ID)")
    telegram_chat_id: str = Field(..., description="텔레그램 채팅 ID", min_length=1, max_length=50)


class TelegramSettings(BaseModel):
    """텔레그램 설정 응답"""
    account_id: str
    telegram_chat_id: str
    is_active: bool


class TelegramTestNotification(BaseModel):
    """테스트 알림"""
    account_id: str = Field(..., description="사용자 계정 ID")


@router.post("/register", response_model=TelegramSettings)
async def register_telegram(telegram: TelegramRegister):
    """
    텔레그램 채팅 ID 등록

    **텔레그램 채팅 ID 찾기**:
    1. 텔레그램 봇과 대화 시작 (/start)
    2. @userinfobot에게 메시지 전송
    3. 봇이 응답한 ID를 복사

    또는 curl로 확인:
    ```bash
    curl https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates
    ```

    **주의**:
    - 반드시 봇과 먼저 대화를 시작해야 알림을 받을 수 있습니다!
    - /start 명령어를 봇에게 보내세요
    """
    try:
        logger.info(f"Registering Telegram for account: {telegram.account_id}")

        # 텔레그램 봇 설정 확인
        if not telegram_service.is_configured():
            raise HTTPException(
                status_code=503,
                detail="Telegram bot not configured. Please set TELEGRAM_BOT_TOKEN in .env"
            )

        # 채팅 ID 유효성 검증 (테스트 메시지 전송)
        is_valid = telegram_service.verify_chat_id(telegram.telegram_chat_id)

        if not is_valid:
            raise HTTPException(
                status_code=400,
                detail="Invalid Telegram chat ID or bot cannot send message to this user. "
                       "Make sure you've started a conversation with the bot (/start)"
            )

        # 메모리에 저장
        user_telegram_settings[telegram.account_id] = telegram.telegram_chat_id

        logger.info(f"Telegram registered successfully: {telegram.account_id} -> {telegram.telegram_chat_id}")

        return TelegramSettings(
            account_id=telegram.account_id,
            telegram_chat_id=telegram.telegram_chat_id,
            is_active=True
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to register Telegram: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{account_id}", response_model=TelegramSettings)
async def get_telegram_settings(account_id: str):
    """
    텔레그램 설정 조회
    """
    chat_id = user_telegram_settings.get(account_id)

    if not chat_id:
        raise HTTPException(
            status_code=404,
            detail=f"Telegram not configured for account: {account_id}"
        )

    return TelegramSettings(
        account_id=account_id,
        telegram_chat_id=chat_id,
        is_active=True
    )


@router.delete("/{account_id}")
async def delete_telegram_settings(account_id: str):
    """
    텔레그램 설정 삭제
    """
    if account_id not in user_telegram_settings:
        raise HTTPException(
            status_code=404,
            detail=f"Telegram not configured for account: {account_id}"
        )

    del user_telegram_settings[account_id]

    logger.info(f"Telegram settings deleted for account: {account_id}")

    return {
        "success": True,
        "message": f"Telegram settings deleted for account: {account_id}"
    }


@router.post("/test", response_model=dict)
async def send_test_notification(test: TelegramTestNotification):
    """
    테스트 알림 전송

    등록된 텔레그램으로 테스트 메시지를 전송합니다.
    """
    chat_id = user_telegram_settings.get(test.account_id)

    if not chat_id:
        raise HTTPException(
            status_code=404,
            detail=f"Telegram not configured for account: {test.account_id}"
        )

    # 테스트 주문 알림 전송
    telegram_service.send_order_notification(
        chat_id=chat_id,
        exchange="binance",
        action="long",
        symbol="BTCUSDT",
        price=67500.0,
        quantity=0.01,
        leverage=3,
        order_id="TEST_ORDER_123"
    )

    return {
        "success": True,
        "message": "Test notification sent successfully",
        "chat_id": chat_id
    }


def get_telegram_chat_id(account_id: str) -> Optional[str]:
    """
    계정 ID로 텔레그램 채팅 ID 조회 (내부 사용)

    Args:
        account_id: 계정 ID

    Returns:
        텔레그램 채팅 ID 또는 None
    """
    return user_telegram_settings.get(account_id)
