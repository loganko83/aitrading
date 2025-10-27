"""
Telegram Notification Service
트레이딩 이벤트 알림 발송
"""
import logging
import aiohttp
from typing import Optional, Dict, Any
from datetime import datetime

from app.core.crypto import crypto_service

logger = logging.getLogger(__name__)


class TelegramService:
    """Telegram Bot API를 통한 알림 발송"""
    
    def __init__(self, bot_token: str, chat_id: str):
        """
        Args:
            bot_token: Telegram Bot Token (암호화된 상태로 전달됨)
            chat_id: Telegram Chat ID (암호화된 상태로 전달됨)
        """
        # 복호화
        decrypted = crypto_service.decrypt_api_credentials({
            "api_key": bot_token,
            "api_secret": chat_id,
            "passphrase": None
        })
        
        self.bot_token = decrypted["api_key"]
        self.chat_id = decrypted["api_secret"]
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
    
    async def send_message(self, text: str, parse_mode: str = "HTML") -> bool:
        """
        Telegram 메시지 발송
        
        Args:
            text: 메시지 내용 (HTML 형식 지원)
            parse_mode: "HTML" 또는 "Markdown"
        
        Returns:
            성공 여부
        """
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "chat_id": self.chat_id,
                    "text": text,
                    "parse_mode": parse_mode
                }
                
                async with session.post(self.api_url, json=payload) as response:
                    if response.status == 200:
                        logger.info(f"Telegram message sent successfully to {self.chat_id}")
                        return True
                    else:
                        error_text = await response.text()
                        logger.error(f"Telegram API error: {response.status} - {error_text}")
                        return False
                        
        except Exception as e:
            logger.error(f"Failed to send Telegram message: {str(e)}", exc_info=True)
            return False
    
    async def notify_entry(self, exchange: str, symbol: str, side: str, 
                          entry_price: float, size: float, leverage: int):
        """
        포지션 진입 알림
        """
        message = f"""
🚀 <b>포지션 진입</b>

거래소: {exchange.upper()}
심볼: {symbol}
방향: {'🟢 LONG' if side == 'LONG' else '🔴 SHORT'}
진입가: ${entry_price:,.2f}
수량: {size}
레버리지: {leverage}x
시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        return await self.send_message(message)
    
    async def notify_exit(self, exchange: str, symbol: str, side: str,
                         entry_price: float, exit_price: float, 
                         pnl: float, pnl_percent: float):
        """
        포지션 청산 알림
        """
        profit_emoji = "📈" if pnl > 0 else "📉"
        message = f"""
{profit_emoji} <b>포지션 청산</b>

거래소: {exchange.upper()}
심볼: {symbol}
방향: {'🟢 LONG' if side == 'LONG' else '🔴 SHORT'}
진입가: ${entry_price:,.2f}
청산가: ${exit_price:,.2f}
수익/손실: ${pnl:,.2f} ({pnl_percent:+.2f}%)
시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        return await self.send_message(message)
    
    async def notify_stop_loss(self, exchange: str, symbol: str, side: str,
                               entry_price: float, sl_price: float, loss: float):
        """
        손절 알림
        """
        message = f"""
⛔️ <b>손절 실행</b>

거래소: {exchange.upper()}
심볼: {symbol}
방향: {'🟢 LONG' if side == 'LONG' else '🔴 SHORT'}
진입가: ${entry_price:,.2f}
손절가: ${sl_price:,.2f}
손실: -${abs(loss):,.2f}
시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        return await self.send_message(message)
    
    async def notify_take_profit(self, exchange: str, symbol: str, side: str,
                                entry_price: float, tp_price: float, profit: float):
        """
        익절 알림
        """
        message = f"""
✅ <b>익절 실행</b>

거래소: {exchange.upper()}
심볼: {symbol}
방향: {'🟢 LONG' if side == 'LONG' else '🔴 SHORT'}
진입가: ${entry_price:,.2f}
익절가: ${tp_price:,.2f}
수익: +${profit:,.2f}
시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        return await self.send_message(message)
    
    async def notify_error(self, error_type: str, message: str):
        """
        에러 알림
        """
        error_message = f"""
❌ <b>에러 발생</b>

유형: {error_type}
메시지: {message}
시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        return await self.send_message(error_message)


async def get_telegram_service(user_id: str, db) -> Optional[TelegramService]:
    """
    사용자의 Telegram 서비스 인스턴스 생성
    
    Args:
        user_id: 사용자 ID
        db: AsyncSession
    
    Returns:
        TelegramService 인스턴스 (설정 없으면 None)
    """
    from sqlalchemy import select
    from app.models.telegram_config import TelegramConfig
    
    result = await db.execute(
        select(TelegramConfig).where(
            TelegramConfig.user_id == user_id,
            TelegramConfig.is_active == True
        )
    )
    config = result.scalar_one_or_none()
    
    if not config:
        logger.warning(f"No active Telegram config for user {user_id}")
        return None
    
    return TelegramService(config.bot_token, config.chat_id)
