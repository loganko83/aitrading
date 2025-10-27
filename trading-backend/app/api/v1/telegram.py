"""
Telegram Configuration API
사용자의 Telegram Bot 설정 관리 (암호화)
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional
import logging

from app.core.auth import get_current_user
from app.database.base import get_db
from app.models.user import User
from app.models.telegram_config import TelegramConfig
from app.core.crypto import crypto_service

router = APIRouter(prefix="/telegram", tags=["Telegram"])
logger = logging.getLogger(__name__)


# ==================== Request/Response Models ====================

class TelegramConfigCreate(BaseModel):
    bot_token: str
    chat_id: str
    notify_entry: bool = True
    notify_exit: bool = True
    notify_stop_loss: bool = True
    notify_take_profit: bool = True


class TelegramConfigResponse(BaseModel):
    id: str
    is_active: bool
    notify_entry: bool
    notify_exit: bool
    notify_stop_loss: bool
    notify_take_profit: bool
    created_at: str
    
    class Config:
        from_attributes = True


# ==================== API Endpoints ====================

@router.post("/register")
async def register_telegram(
    data: TelegramConfigCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Telegram Bot 설정 등록
    
    **보안:**
    - bot_token과 chat_id는 AES-256으로 암호화되어 저장됨
    """
    try:
        # 기존 설정 확인
        result = await db.execute(
            select(TelegramConfig).where(TelegramConfig.user_id == current_user.id)
        )
        existing = result.scalar_one_or_none()
        
        # Telegram API 키 암호화
        encrypted = crypto_service.encrypt_api_credentials({
            "api_key": data.bot_token,
            "api_secret": data.chat_id,
            "passphrase": None
        })
        
        if existing:
            # Update
            existing.bot_token = encrypted["api_key"]
            existing.chat_id = encrypted["api_secret"]
            existing.notify_entry = data.notify_entry
            existing.notify_exit = data.notify_exit
            existing.notify_stop_loss = data.notify_stop_loss
            existing.notify_take_profit = data.notify_take_profit
            existing.is_active = True
            
            telegram_config = existing
        else:
            # Create new
            telegram_config = TelegramConfig(
                user_id=current_user.id,
                bot_token=encrypted["api_key"],
                chat_id=encrypted["api_secret"],
                notify_entry=data.notify_entry,
                notify_exit=data.notify_exit,
                notify_stop_loss=data.notify_stop_loss,
                notify_take_profit=data.notify_take_profit
            )
            db.add(telegram_config)
        
        await db.commit()
        await db.refresh(telegram_config)
        
        return {
            "id": telegram_config.id,
            "is_active": telegram_config.is_active,
            "message": "Telegram configuration saved successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to register Telegram config: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/config")
async def get_telegram_config(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    사용자의 Telegram 설정 조회
    """
    result = await db.execute(
        select(TelegramConfig).where(TelegramConfig.user_id == current_user.id)
    )
    config = result.scalar_one_or_none()
    
    if not config:
        raise HTTPException(status_code=404, detail="Telegram not configured")
    
    return {
        "id": config.id,
        "is_active": config.is_active,
        "notify_entry": config.notify_entry,
        "notify_exit": config.notify_exit,
        "notify_stop_loss": config.notify_stop_loss,
        "notify_take_profit": config.notify_take_profit,
        "created_at": config.created_at.isoformat()
    }


@router.post("/toggle")
async def toggle_telegram(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Telegram 알림 활성화/비활성화
    """
    result = await db.execute(
        select(TelegramConfig).where(TelegramConfig.user_id == current_user.id)
    )
    config = result.scalar_one_or_none()
    
    if not config:
        raise HTTPException(status_code=404, detail="Telegram not configured")
    
    config.is_active = not config.is_active
    await db.commit()
    
    return {
        "id": config.id,
        "is_active": config.is_active,
        "message": f"Telegram notifications {'enabled' if config.is_active else 'disabled'}"
    }


@router.delete("/delete")
async def delete_telegram_config(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Telegram 설정 삭제
    """
    result = await db.execute(
        select(TelegramConfig).where(TelegramConfig.user_id == current_user.id)
    )
    config = result.scalar_one_or_none()
    
    if not config:
        raise HTTPException(status_code=404, detail="Telegram not configured")
    
    await db.delete(config)
    await db.commit()
    
    return {"success": True, "message": "Telegram configuration deleted"}
