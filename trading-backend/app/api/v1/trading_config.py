from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
import logging
import uuid

from app.core.auth import get_current_user
from app.database.session import get_db
from app.models.user import User
from app.models.trading_config import TradingConfig, InvestmentType
from app.models.api_key import ApiKey

router = APIRouter()
logger = logging.getLogger(__name__)


class TradingConfigCreate(BaseModel):
    api_key_id: str = Field(..., description="API Key ID for which exchange account to use")
    strategy: Optional[str] = Field(None, description="Strategy name (optional)")
    investment_type: InvestmentType = Field(InvestmentType.PERCENTAGE, description="percentage or fixed")
    investment_value: float = Field(..., gt=0, description="0.1 = 10% or 100 = 100 USDT")
    leverage: float = Field(10.0, ge=1, le=125)
    stop_loss_percentage: float = Field(2.0, gt=0)
    take_profit_percentage: float = Field(5.0, gt=0)
    is_active: bool = Field(True)


class TradingConfigUpdate(BaseModel):
    strategy: Optional[str] = None
    investment_type: Optional[InvestmentType] = None
    investment_value: Optional[float] = Field(None, gt=0)
    leverage: Optional[float] = Field(None, ge=1, le=125)
    stop_loss_percentage: Optional[float] = Field(None, gt=0)
    take_profit_percentage: Optional[float] = Field(None, gt=0)
    is_active: Optional[bool] = None


class TradingConfigResponse(BaseModel):
    id: str
    user_id: str
    api_key_id: str
    exchange: str  # From related ApiKey
    strategy: Optional[str]
    investment_type: str
    investment_value: float
    leverage: float
    stop_loss_percentage: float
    take_profit_percentage: float
    is_active: bool
    created_at: datetime
    updated_at: datetime


@router.post("/", response_model=TradingConfigResponse)
async def create_trading_config(
    config_data: TradingConfigCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Trading Bot 설정 생성

    - 비율 기반 투자: investment_type="percentage", investment_value=0.1 (10%)
    - 고정 금액 투자: investment_type="fixed", investment_value=100 (100 USDT)
    """
    try:
        # Verify API key belongs to current user
        stmt = select(ApiKey).where(
            ApiKey.id == config_data.api_key_id,
            ApiKey.user_id == current_user.id,
            ApiKey.is_active == True
        )
        result = await db.execute(stmt)
        api_key = result.scalar_one_or_none()

        if not api_key:
            raise HTTPException(status_code=404, detail="API key not found or inactive")

        # Create new config
        new_config = TradingConfig(
            id=str(uuid.uuid4()),
            user_id=current_user.id,
            api_key_id=config_data.api_key_id,
            strategy=config_data.strategy,
            investment_type=config_data.investment_type,
            investment_value=config_data.investment_value,
            leverage=config_data.leverage,
            stop_loss_percentage=config_data.stop_loss_percentage,
            take_profit_percentage=config_data.take_profit_percentage,
            is_active=config_data.is_active
        )

        db.add(new_config)
        await db.commit()
        await db.refresh(new_config)

        return TradingConfigResponse(
            id=new_config.id,
            user_id=new_config.user_id,
            api_key_id=new_config.api_key_id,
            exchange=api_key.exchange,
            strategy=new_config.strategy,
            investment_type=new_config.investment_type.value,
            investment_value=new_config.investment_value,
            leverage=new_config.leverage,
            stop_loss_percentage=new_config.stop_loss_percentage,
            take_profit_percentage=new_config.take_profit_percentage,
            is_active=new_config.is_active,
            created_at=new_config.created_at,
            updated_at=new_config.updated_at
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create trading config: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create trading config: {str(e)}")


@router.get("/", response_model=List[TradingConfigResponse])
async def list_trading_configs(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """현재 사용자의 모든 Trading Bot 설정 조회"""
    try:
        stmt = select(TradingConfig, ApiKey).join(
            ApiKey, TradingConfig.api_key_id == ApiKey.id
        ).where(
            TradingConfig.user_id == current_user.id
        ).order_by(TradingConfig.created_at.desc())

        result = await db.execute(stmt)
        rows = result.all()

        configs = []
        for config, api_key in rows:
            configs.append(TradingConfigResponse(
                id=config.id,
                user_id=config.user_id,
                api_key_id=config.api_key_id,
                exchange=api_key.exchange,
                strategy=config.strategy,
                investment_type=config.investment_type.value,
                investment_value=config.investment_value,
                leverage=config.leverage,
                stop_loss_percentage=config.stop_loss_percentage,
                take_profit_percentage=config.take_profit_percentage,
                is_active=config.is_active,
                created_at=config.created_at,
                updated_at=config.updated_at
            ))

        return configs

    except Exception as e:
        logger.error(f"Failed to list trading configs: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{config_id}", response_model=TradingConfigResponse)
async def get_trading_config(
    config_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """특정 Trading Bot 설정 조회"""
    try:
        stmt = select(TradingConfig, ApiKey).join(
            ApiKey, TradingConfig.api_key_id == ApiKey.id
        ).where(
            TradingConfig.id == config_id,
            TradingConfig.user_id == current_user.id
        )
        result = await db.execute(stmt)
        row = result.one_or_none()

        if not row:
            raise HTTPException(status_code=404, detail="Trading config not found")

        config, api_key = row

        return TradingConfigResponse(
            id=config.id,
            user_id=config.user_id,
            api_key_id=config.api_key_id,
            exchange=api_key.exchange,
            strategy=config.strategy,
            investment_type=config.investment_type.value,
            investment_value=config.investment_value,
            leverage=config.leverage,
            stop_loss_percentage=config.stop_loss_percentage,
            take_profit_percentage=config.take_profit_percentage,
            is_active=config.is_active,
            created_at=config.created_at,
            updated_at=config.updated_at
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get trading config: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{config_id}", response_model=TradingConfigResponse)
async def update_trading_config(
    config_id: str,
    config_data: TradingConfigUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Trading Bot 설정 수정"""
    try:
        stmt = select(TradingConfig, ApiKey).join(
            ApiKey, TradingConfig.api_key_id == ApiKey.id
        ).where(
            TradingConfig.id == config_id,
            TradingConfig.user_id == current_user.id
        )
        result = await db.execute(stmt)
        row = result.one_or_none()

        if not row:
            raise HTTPException(status_code=404, detail="Trading config not found")

        config, api_key = row

        # Update only provided fields
        update_data = config_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(config, key, value)

        config.updated_at = datetime.utcnow()

        await db.commit()
        await db.refresh(config)

        return TradingConfigResponse(
            id=config.id,
            user_id=config.user_id,
            api_key_id=config.api_key_id,
            exchange=api_key.exchange,
            strategy=config.strategy,
            investment_type=config.investment_type.value,
            investment_value=config.investment_value,
            leverage=config.leverage,
            stop_loss_percentage=config.stop_loss_percentage,
            take_profit_percentage=config.take_profit_percentage,
            is_active=config.is_active,
            created_at=config.created_at,
            updated_at=config.updated_at
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update trading config: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{config_id}")
async def delete_trading_config(
    config_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Trading Bot 설정 삭제"""
    try:
        stmt = select(TradingConfig).where(
            TradingConfig.id == config_id,
            TradingConfig.user_id == current_user.id
        )
        result = await db.execute(stmt)
        config = result.scalar_one_or_none()

        if not config:
            raise HTTPException(status_code=404, detail="Trading config not found")

        await db.delete(config)
        await db.commit()

        return {"success": True, "message": "Trading config deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete trading config: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{config_id}/toggle")
async def toggle_trading_config(
    config_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Trading Bot 설정 활성화/비활성화"""
    try:
        stmt = select(TradingConfig).where(
            TradingConfig.id == config_id,
            TradingConfig.user_id == current_user.id
        )
        result = await db.execute(stmt)
        config = result.scalar_one_or_none()

        if not config:
            raise HTTPException(status_code=404, detail="Trading config not found")

        config.is_active = not config.is_active
        config.updated_at = datetime.utcnow()

        await db.commit()

        return {
            "success": True,
            "config_id": config.id,
            "is_active": config.is_active
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to toggle trading config: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
