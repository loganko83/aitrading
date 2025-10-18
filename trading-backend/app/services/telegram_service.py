"""
Telegram Notification Service

Features:
- 실시간 주문 알림
- 포지션 진입/청산 알림
- 손익 변화 알림
- Webhook 수신 알림
"""

import requests
import logging
from typing import Optional, Dict, Any
from datetime import datetime

from app.core.config import settings

logger = logging.getLogger(__name__)


class TelegramService:
    """텔레그램 알림 서비스"""

    def __init__(self):
        self.bot_token = getattr(settings, 'TELEGRAM_BOT_TOKEN', None)
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}" if self.bot_token else None

    def is_configured(self) -> bool:
        """텔레그램 봇 설정 여부 확인"""
        return self.bot_token is not None and self.bot_token != ""

    def send_message(
        self,
        chat_id: str,
        message: str,
        parse_mode: str = "HTML",
        disable_notification: bool = False
    ) -> bool:
        """
        텔레그램 메시지 전송

        Args:
            chat_id: 텔레그램 채팅 ID
            message: 전송할 메시지
            parse_mode: 메시지 형식 (HTML, Markdown)
            disable_notification: 무음 알림 여부

        Returns:
            성공 여부
        """
        if not self.is_configured():
            logger.warning("Telegram bot not configured. Skipping notification.")
            return False

        try:
            url = f"{self.base_url}/sendMessage"
            payload = {
                "chat_id": chat_id,
                "text": message,
                "parse_mode": parse_mode,
                "disable_notification": disable_notification
            }

            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()

            logger.info(f"Telegram message sent to {chat_id}")
            return True

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send Telegram message: {str(e)}", exc_info=True)
            return False

    def send_order_notification(
        self,
        chat_id: str,
        exchange: str,
        action: str,
        symbol: str,
        price: Optional[float] = None,
        quantity: Optional[float] = None,
        leverage: Optional[int] = None,
        order_id: Optional[str] = None
    ):
        """
        주문 실행 알림

        예시:
        🚀 롱 진입!
        거래소: Binance Futures
        심볼: BTCUSDT
        가격: $67,500
        수량: 0.01 BTC
        레버리지: 3x
        """
        # 액션별 이모지 및 제목
        action_map = {
            "long": ("🚀", "롱 진입"),
            "short": ("📉", "숏 진입"),
            "close_long": ("✅", "롱 포지션 청산"),
            "close_short": ("✅", "숏 포지션 청산"),
            "close_all": ("🛑", "모든 포지션 청산")
        }

        emoji, title = action_map.get(action.lower(), ("📊", "주문 실행"))

        message_parts = [
            f"{emoji} <b>{title}</b>",
            f"",
            f"📍 거래소: {exchange.upper()}",
            f"💰 심볼: {symbol}",
        ]

        if price:
            message_parts.append(f"💵 가격: ${price:,.2f}")

        if quantity:
            message_parts.append(f"📊 수량: {quantity} BTC")

        if leverage:
            message_parts.append(f"⚡ 레버리지: {leverage}x")

        if order_id:
            message_parts.append(f"🔖 주문 ID: <code>{order_id}</code>")

        message_parts.append(f"")
        message_parts.append(f"🕒 시간: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")

        message = "\n".join(message_parts)
        self.send_message(chat_id, message)

    def send_webhook_received_notification(
        self,
        chat_id: str,
        exchange: str,
        action: str,
        symbol: str,
        success: bool = True,
        error_message: Optional[str] = None
    ):
        """
        Webhook 수신 알림

        예시:
        📡 TradingView 시그널 수신
        거래소: Binance
        액션: long
        심볼: BTCUSDT
        상태: ✅ 성공
        """
        if success:
            emoji = "✅"
            status = "성공"
        else:
            emoji = "❌"
            status = f"실패 - {error_message}"

        message = (
            f"📡 <b>TradingView 시그널 수신</b>\n"
            f"\n"
            f"📍 거래소: {exchange.upper()}\n"
            f"📊 액션: {action.upper()}\n"
            f"💰 심볼: {symbol}\n"
            f"📌 상태: {emoji} {status}\n"
            f"\n"
            f"🕒 {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC"
        )

        self.send_message(chat_id, message)

    def send_position_update(
        self,
        chat_id: str,
        symbol: str,
        side: str,
        entry_price: float,
        current_price: float,
        quantity: float,
        leverage: int,
        pnl: float,
        pnl_percent: float
    ):
        """
        포지션 업데이트 알림

        예시:
        📊 포지션 현황
        심볼: BTCUSDT
        방향: 롱
        진입가: $67,000
        현재가: $67,500
        손익: +$15.00 (+2.24%)
        """
        if pnl >= 0:
            pnl_emoji = "📈"
            pnl_sign = "+"
        else:
            pnl_emoji = "📉"
            pnl_sign = ""

        message = (
            f"📊 <b>포지션 현황</b>\n"
            f"\n"
            f"💰 심볼: {symbol}\n"
            f"📍 방향: {'롱 🚀' if side.upper() == 'LONG' else '숏 📉'}\n"
            f"💵 진입가: ${entry_price:,.2f}\n"
            f"💵 현재가: ${current_price:,.2f}\n"
            f"📊 수량: {quantity} BTC\n"
            f"⚡ 레버리지: {leverage}x\n"
            f"\n"
            f"{pnl_emoji} <b>손익: {pnl_sign}${pnl:,.2f} ({pnl_sign}{pnl_percent:.2f}%)</b>\n"
            f"\n"
            f"🕒 {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC"
        )

        # 손익에 따라 무음 알림 설정
        disable_notification = abs(pnl_percent) < 1.0  # 1% 미만 변화는 무음

        self.send_message(chat_id, message, disable_notification=disable_notification)

    def send_error_notification(
        self,
        chat_id: str,
        error_type: str,
        error_message: str,
        context: Optional[Dict[str, Any]] = None
    ):
        """
        에러 알림

        예시:
        ⚠️ 에러 발생!
        유형: 주문 실행 실패
        메시지: Insufficient balance
        """
        message_parts = [
            f"⚠️ <b>에러 발생</b>",
            f"",
            f"🔴 유형: {error_type}",
            f"📝 메시지: {error_message}",
        ]

        if context:
            message_parts.append(f"")
            message_parts.append(f"📋 상세 정보:")
            for key, value in context.items():
                message_parts.append(f"  • {key}: {value}")

        message_parts.append(f"")
        message_parts.append(f"🕒 {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")

        message = "\n".join(message_parts)
        self.send_message(chat_id, message)

    def verify_chat_id(self, chat_id: str) -> bool:
        """
        텔레그램 채팅 ID 유효성 검증

        Args:
            chat_id: 검증할 채팅 ID

        Returns:
            유효 여부
        """
        if not self.is_configured():
            return False

        try:
            # 테스트 메시지 전송 (무음)
            test_message = "✅ 텔레그램 알림 설정이 완료되었습니다!"
            return self.send_message(chat_id, test_message, disable_notification=False)

        except Exception as e:
            logger.error(f"Failed to verify Telegram chat ID: {str(e)}")
            return False


# 싱글톤 인스턴스
telegram_service = TelegramService()
