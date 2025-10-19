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

    # ===== Enhanced Position Notifications =====

    def send_position_entry_notification(
        self,
        chat_id: str,
        symbol: str,
        side: str,
        entry_price: float,
        quantity: float,
        leverage: int,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
        risk_percent: Optional[float] = None
    ):
        """
        포지션 진입 상세 알림 (강화 버전)

        예시:
        🚀 롱 포지션 진입!
        심볼: BTCUSDT
        진입가: $67,500
        수량: 0.01 BTC
        레버리지: 3x
        손절가: $66,800 (-1.04%)
        익절가: $68,500 (+1.48%)
        리스크: 2.5% of portfolio
        """
        emoji = "🚀" if side.upper() == "LONG" else "📉"
        title = f"{emoji} <b>{side.upper()} 포지션 진입!</b>"

        message_parts = [
            title,
            "",
            f"💰 심볼: {symbol}",
            f"💵 진입가: ${entry_price:,.2f}",
            f"📊 수량: {quantity:.6f}",
            f"⚡ 레버리지: {leverage}x",
        ]

        # Stop loss information
        if stop_loss:
            sl_percent = ((stop_loss - entry_price) / entry_price) * 100
            message_parts.append(f"🛑 손절가: ${stop_loss:,.2f} ({sl_percent:+.2f}%)")

        # Take profit information
        if take_profit:
            tp_percent = ((take_profit - entry_price) / entry_price) * 100
            message_parts.append(f"🎯 익절가: ${take_profit:,.2f} ({tp_percent:+.2f}%)")

        # Risk-reward ratio
        if stop_loss and take_profit:
            risk = abs(entry_price - stop_loss)
            reward = abs(take_profit - entry_price)
            rr_ratio = reward / risk if risk > 0 else 0
            message_parts.append(f"⚖️ R:R 비율: 1:{rr_ratio:.2f}")

        # Portfolio risk
        if risk_percent:
            message_parts.append(f"📊 포트폴리오 리스크: {risk_percent:.2f}%")

        message_parts.extend([
            "",
            f"🕒 {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC"
        ])

        message = "\n".join(message_parts)
        self.send_message(chat_id, message)

    def send_position_exit_notification(
        self,
        chat_id: str,
        symbol: str,
        side: str,
        entry_price: float,
        exit_price: float,
        quantity: float,
        leverage: int,
        pnl: float,
        pnl_percent: float,
        exit_reason: str,
        holding_time: Optional[str] = None
    ):
        """
        포지션 청산 상세 알림 (강화 버전)

        예시:
        ✅ 롱 포지션 청산!
        심볼: BTCUSDT
        진입가: $67,000
        청산가: $68,500
        손익: +$45.00 (+2.24%)
        청산 사유: Take profit hit
        보유 시간: 2h 15m
        """
        if pnl >= 0:
            emoji = "✅💰"
            title_suffix = "수익 실현"
        else:
            emoji = "❌"
            title_suffix = "손실 확정"

        message_parts = [
            f"{emoji} <b>{side.upper()} 포지션 청산 - {title_suffix}</b>",
            "",
            f"💰 심볼: {symbol}",
            f"💵 진입가: ${entry_price:,.2f}",
            f"💵 청산가: ${exit_price:,.2f}",
            f"📊 수량: {quantity:.6f}",
            f"⚡ 레버리지: {leverage}x",
            "",
        ]

        # P&L with color coding
        pnl_sign = "+" if pnl >= 0 else ""
        if pnl >= 0:
            message_parts.append(f"📈 <b>손익: {pnl_sign}${pnl:,.2f} ({pnl_sign}{pnl_percent:.2f}%)</b>")
        else:
            message_parts.append(f"📉 <b>손익: {pnl_sign}${pnl:,.2f} ({pnl_sign}{pnl_percent:.2f}%)</b>")

        message_parts.append("")
        message_parts.append(f"📌 청산 사유: {exit_reason}")

        if holding_time:
            message_parts.append(f"⏱️ 보유 시간: {holding_time}")

        message_parts.extend([
            "",
            f"🕒 {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC"
        ])

        message = "\n".join(message_parts)
        self.send_message(chat_id, message)

    # ===== Risk Alert Notifications =====

    def send_var_alert(
        self,
        chat_id: str,
        current_var: float,
        threshold_var: float,
        confidence_level: float,
        portfolio_value: float
    ):
        """
        VaR 임계값 초과 경고

        예시:
        🚨 VaR 경고!
        현재 VaR: $850 (8.5%)
        설정 임계값: $750 (7.5%)
        신뢰 수준: 95%
        포트폴리오 가치: $10,000
        """
        var_percent = (current_var / portfolio_value) * 100 if portfolio_value > 0 else 0
        threshold_percent = (threshold_var / portfolio_value) * 100 if portfolio_value > 0 else 0

        message = (
            f"🚨 <b>VaR 경고!</b>\n"
            f"\n"
            f"⚠️ 현재 VaR: ${current_var:,.2f} ({var_percent:.2f}%)\n"
            f"📊 설정 임계값: ${threshold_var:,.2f} ({threshold_percent:.2f}%)\n"
            f"📈 신뢰 수준: {confidence_level * 100:.0f}%\n"
            f"💰 포트폴리오 가치: ${portfolio_value:,.2f}\n"
            f"\n"
            f"💡 <b>권장 조치:</b>\n"
            f"  • 포지션 규모 축소 고려\n"
            f"  • 레버리지 감소\n"
            f"  • 손절매 설정 확인\n"
            f"\n"
            f"🕒 {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC"
        )

        self.send_message(chat_id, message)

    def send_liquidation_warning(
        self,
        chat_id: str,
        symbol: str,
        side: str,
        entry_price: float,
        current_price: float,
        liquidation_price: float,
        distance_percent: float,
        leverage: int
    ):
        """
        청산가 근접 경고

        예시:
        🚨 청산 위험!
        심볼: BTCUSDT (롱)
        현재가: $67,000
        청산가: $66,200
        거리: 1.19% (매우 위험!)
        레버리지: 10x
        """
        # Determine danger level
        if distance_percent <= 5:
            danger_emoji = "🚨🚨🚨"
            danger_level = "극도로 위험!"
        elif distance_percent <= 10:
            danger_emoji = "🚨🚨"
            danger_level = "매우 위험!"
        elif distance_percent <= 15:
            danger_emoji = "⚠️"
            danger_level = "위험"
        else:
            danger_emoji = "⚠️"
            danger_level = "주의"

        message = (
            f"{danger_emoji} <b>청산 위험 경고 - {danger_level}</b>\n"
            f"\n"
            f"💰 심볼: {symbol}\n"
            f"📍 방향: {'롱 🚀' if side.upper() == 'LONG' else '숏 📉'}\n"
            f"💵 진입가: ${entry_price:,.2f}\n"
            f"💵 현재가: ${current_price:,.2f}\n"
            f"🔴 청산가: ${liquidation_price:,.2f}\n"
            f"📏 거리: <b>{distance_percent:.2f}%</b>\n"
            f"⚡ 레버리지: {leverage}x\n"
            f"\n"
            f"💡 <b>긴급 조치 필요:</b>\n"
            f"  • 즉시 증거금 추가 또는\n"
            f"  • 포지션 일부/전체 청산\n"
            f"  • 레버리지 감소 고려\n"
            f"\n"
            f"🕒 {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC"
        )

        # Always send as high-priority notification
        self.send_message(chat_id, message, disable_notification=False)

    def send_concentration_warning(
        self,
        chat_id: str,
        largest_position_pct: float,
        top_3_concentration: float,
        total_positions: int,
        herfindahl_index: float
    ):
        """
        포지션 집중도 경고

        예시:
        ⚠️ 포지션 집중도 경고
        최대 포지션 비율: 45%
        Top 3 집중도: 85%
        총 포지션 수: 4개
        다각화 부족 - 리스크 분산 권장
        """
        message_parts = [
            "⚠️ <b>포지션 집중도 경고</b>",
            "",
            f"📊 최대 포지션 비율: <b>{largest_position_pct:.2f}%</b>",
            f"📈 Top 3 집중도: <b>{top_3_concentration:.2f}%</b>",
            f"📋 총 포지션 수: {total_positions}개",
            f"📉 HHI 지수: {herfindahl_index:.0f}",
            "",
        ]

        # Risk assessment
        if largest_position_pct > 40:
            message_parts.append("🚨 <b>위험:</b> 단일 포지션이 과도하게 큽니다")
        elif largest_position_pct > 30:
            message_parts.append("⚠️ <b>주의:</b> 포지션 집중도가 높습니다")

        if top_3_concentration > 80:
            message_parts.append("🚨 <b>위험:</b> 상위 3개 포지션 집중도 과다")

        message_parts.extend([
            "",
            "💡 <b>권장 조치:</b>",
            "  • 대형 포지션 축소",
            "  • 다각화 증대",
            "  • 리밸런싱 고려",
            "",
            f"🕒 {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC"
        ])

        message = "\n".join(message_parts)
        self.send_message(chat_id, message)

    def send_daily_risk_report(
        self,
        chat_id: str,
        portfolio_value: float,
        total_exposure: float,
        var_amount: float,
        var_percentage: float,
        max_drawdown_pct: float,
        total_positions: int,
        winning_positions: int,
        losing_positions: int,
        daily_pnl: float,
        daily_pnl_pct: float
    ):
        """
        일일 리스크 리포트

        예시:
        📊 일일 리스크 리포트
        날짜: 2025-01-18

        포트폴리오 현황:
        총 가치: $10,250
        총 노출: $30,750 (3x avg leverage)
        오늘 손익: +$125 (+1.23%)

        리스크 지표:
        VaR (95%): $850 (8.3%)
        최대 낙폭: -12.5%
        포지션 수: 4개 (수익 3개, 손실 1개)

        상태: ✅ 정상
        """
        # Determine status
        if var_percentage > 10 or max_drawdown_pct > 20:
            status = "🚨 위험"
        elif var_percentage > 7.5 or max_drawdown_pct > 15:
            status = "⚠️ 주의"
        else:
            status = "✅ 정상"

        # Daily P&L emoji
        pnl_emoji = "📈" if daily_pnl >= 0 else "📉"
        pnl_sign = "+" if daily_pnl >= 0 else ""

        message = (
            f"📊 <b>일일 리스크 리포트</b>\n"
            f"📅 날짜: {datetime.utcnow().strftime('%Y-%m-%d')}\n"
            f"\n"
            f"<b>포트폴리오 현황:</b>\n"
            f"💰 총 가치: ${portfolio_value:,.2f}\n"
            f"📊 총 노출: ${total_exposure:,.2f}\n"
            f"{pnl_emoji} 오늘 손익: {pnl_sign}${daily_pnl:,.2f} ({pnl_sign}{daily_pnl_pct:.2f}%)\n"
            f"\n"
            f"<b>리스크 지표:</b>\n"
            f"📉 VaR (95%): ${var_amount:,.2f} ({var_percentage:.2f}%)\n"
            f"📊 최대 낙폭: {max_drawdown_pct:.2f}%\n"
            f"📋 포지션 수: {total_positions}개\n"
            f"  ├─ 수익: {winning_positions}개 💚\n"
            f"  └─ 손실: {losing_positions}개 ❤️\n"
            f"\n"
            f"<b>상태: {status}</b>\n"
            f"\n"
            f"🕒 {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC"
        )

        # Use quiet notification for routine daily reports
        self.send_message(chat_id, message, disable_notification=True)


# 싱글톤 인스턴스
telegram_service = TelegramService()
