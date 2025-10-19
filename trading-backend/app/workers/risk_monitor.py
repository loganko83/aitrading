"""
리스크 모니터링 백그라운드 워커

주기적으로 포트폴리오 리스크를 모니터링하고 임계값 초과 시 알림을 전송합니다.
"""

import asyncio
import logging
from datetime import datetime, time
from typing import Dict, List, Optional, Set

from app.core.config import settings
from app.services.telegram_service import TelegramService
from app.services.binance_client import BinanceClient
from app.services.okx_client import OKXClient
from app.models.api_key import ApiKey
from app.database.session import get_db
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class RiskMonitorConfig:
    """리스크 모니터링 설정"""

    # VaR 임계값 (포트폴리오 가치 대비 %)
    VAR_WARNING_THRESHOLD = 7.5
    VAR_DANGER_THRESHOLD = 10.0

    # 청산가 근접 경고 임계값 (%)
    LIQUIDATION_WARNING_THRESHOLD = 15.0
    LIQUIDATION_DANGER_THRESHOLD = 10.0
    LIQUIDATION_CRITICAL_THRESHOLD = 5.0

    # 포지션 집중도 임계값
    SINGLE_POSITION_WARNING = 30.0  # 단일 포지션이 30% 초과
    SINGLE_POSITION_DANGER = 40.0   # 단일 포지션이 40% 초과
    TOP3_CONCENTRATION_WARNING = 60.0  # 상위 3개 포지션이 60% 초과
    TOP3_CONCENTRATION_DANGER = 75.0   # 상위 3개 포지션이 75% 초과

    # 최대 낙폭 임계값
    MAX_DRAWDOWN_WARNING = 15.0
    MAX_DRAWDOWN_DANGER = 20.0

    # 모니터링 간격 (초)
    MONITORING_INTERVAL = 60  # 1분마다 체크

    # 일일 리포트 전송 시간 (UTC)
    DAILY_REPORT_TIME = time(23, 0)  # UTC 23:00 = KST 08:00 (다음날 아침)

    # 중복 알림 방지 (같은 이슈는 N분마다만 알림)
    ALERT_COOLDOWN_MINUTES = 30


class RiskMonitor:
    """리스크 모니터링 서비스"""

    def __init__(self):
        self.telegram = TelegramService()
        self.config = RiskMonitorConfig()

        # 마지막 알림 시간 추적 (중복 방지)
        self.last_alerts: Dict[str, datetime] = {}

        # 일일 리포트 전송 추적
        self.last_daily_report_date: Optional[datetime] = None

        # 활성 상태
        self.is_running = False

    async def start(self):
        """모니터링 시작"""
        self.is_running = True
        logger.info("🚀 Risk monitoring service started")

        while self.is_running:
            try:
                # 모든 활성 계정 모니터링
                await self.monitor_all_accounts()

                # 일일 리포트 체크
                await self.check_daily_report()

            except Exception as e:
                logger.error(f"Risk monitoring error: {e}", exc_info=True)

            # 다음 체크까지 대기
            await asyncio.sleep(self.config.MONITORING_INTERVAL)

    async def stop(self):
        """모니터링 중지"""
        self.is_running = False
        logger.info("🛑 Risk monitoring service stopped")

    async def monitor_all_accounts(self):
        """모든 활성 계정 모니터링"""
        db: Session = next(get_db())

        try:
            # 모든 활성 API 키 조회
            active_keys = db.query(ApiKey).filter(
                ApiKey.is_active == True
            ).all()

            for api_key in active_keys:
                try:
                    await self.monitor_account(api_key, db)
                except Exception as e:
                    logger.error(f"Error monitoring account {api_key.id}: {e}")

        finally:
            db.close()

    async def monitor_account(self, api_key: ApiKey, db: Session):
        """개별 계정 모니터링"""

        # 거래소 클라이언트 생성
        if api_key.exchange == "binance":
            client = BinanceClient(
                api_key=api_key.api_key,
                api_secret=api_key.api_secret,
                testnet=api_key.testnet
            )
        elif api_key.exchange == "okx":
            client = OKXClient(
                api_key=api_key.api_key,
                api_secret=api_key.api_secret,
                passphrase=api_key.passphrase,
                testnet=api_key.testnet
            )
        else:
            logger.warning(f"Unsupported exchange: {api_key.exchange}")
            return

        # 계정 정보 조회
        try:
            balance_info = await client.get_account_balance()
            positions = await client.get_positions()

            # 텔레그램 채팅 ID (User와 연결되어야 함, 여기서는 간단히 구현)
            # 실제로는 User 모델에 telegram_chat_id 필드 추가 필요
            chat_id = getattr(api_key.user, 'telegram_chat_id', None)

            if not chat_id:
                # 텔레그램 미설정 시 스킵
                return

            # 포트폴리오 가치
            total_balance = float(balance_info.get('totalWalletBalance', 0))

            # 활성 포지션 필터링
            active_positions = [p for p in positions if float(p.get('positionAmt', 0)) != 0]

            if not active_positions:
                # 포지션 없으면 스킵
                return

            # 1. VaR 체크
            await self.check_var(
                api_key=api_key,
                chat_id=chat_id,
                total_balance=total_balance,
                positions=active_positions
            )

            # 2. 청산가 근접 체크
            await self.check_liquidation_proximity(
                api_key=api_key,
                chat_id=chat_id,
                positions=active_positions
            )

            # 3. 포지션 집중도 체크
            await self.check_position_concentration(
                api_key=api_key,
                chat_id=chat_id,
                total_balance=total_balance,
                positions=active_positions
            )

        except Exception as e:
            logger.error(f"Error monitoring account {api_key.id}: {e}")

    async def check_var(
        self,
        api_key: ApiKey,
        chat_id: str,
        total_balance: float,
        positions: List[Dict]
    ):
        """VaR (Value at Risk) 체크"""

        # 간단한 VaR 추정: 총 노출의 5% (95% 신뢰수준)
        total_exposure = sum(
            abs(float(p.get('notional', 0)))
            for p in positions
        )

        # VaR = 총 노출 * 5% (가정: 95% 신뢰수준에서 일일 변동성 5%)
        var_amount = total_exposure * 0.05
        var_percentage = (var_amount / total_balance * 100) if total_balance > 0 else 0

        # 임계값 체크
        alert_key = f"{api_key.id}_var"

        if var_percentage > self.config.VAR_DANGER_THRESHOLD:
            if self._should_send_alert(alert_key):
                self.telegram.send_var_alert(
                    chat_id=chat_id,
                    current_var_amount=var_amount,
                    current_var_percentage=var_percentage,
                    threshold_percentage=self.config.VAR_DANGER_THRESHOLD,
                    confidence_level=95
                )
                self._mark_alert_sent(alert_key)
                logger.warning(
                    f"VaR alert sent for account {api_key.id}: "
                    f"{var_percentage:.2f}% (threshold: {self.config.VAR_DANGER_THRESHOLD}%)"
                )

        elif var_percentage > self.config.VAR_WARNING_THRESHOLD:
            if self._should_send_alert(alert_key):
                self.telegram.send_var_alert(
                    chat_id=chat_id,
                    current_var_amount=var_amount,
                    current_var_percentage=var_percentage,
                    threshold_percentage=self.config.VAR_WARNING_THRESHOLD,
                    confidence_level=95
                )
                self._mark_alert_sent(alert_key)
                logger.info(
                    f"VaR warning sent for account {api_key.id}: "
                    f"{var_percentage:.2f}% (threshold: {self.config.VAR_WARNING_THRESHOLD}%)"
                )

    async def check_liquidation_proximity(
        self,
        api_key: ApiKey,
        chat_id: str,
        positions: List[Dict]
    ):
        """청산가 근접 체크"""

        for position in positions:
            try:
                symbol = position.get('symbol')
                side = 'long' if float(position.get('positionAmt', 0)) > 0 else 'short'
                entry_price = float(position.get('entryPrice', 0))
                mark_price = float(position.get('markPrice', 0))
                liquidation_price = float(position.get('liquidationPrice', 0))
                leverage = int(position.get('leverage', 1))

                if liquidation_price == 0:
                    continue

                # 청산가까지 거리 계산
                if side == 'long':
                    distance = ((mark_price - liquidation_price) / mark_price * 100)
                else:
                    distance = ((liquidation_price - mark_price) / mark_price * 100)

                # 임계값 체크
                alert_key = f"{api_key.id}_liquidation_{symbol}"

                if distance <= self.config.LIQUIDATION_CRITICAL_THRESHOLD:
                    # 항상 알림 (매우 위험)
                    self.telegram.send_liquidation_warning(
                        chat_id=chat_id,
                        symbol=symbol,
                        side=side,
                        entry_price=entry_price,
                        current_price=mark_price,
                        liquidation_price=liquidation_price,
                        distance_percent=distance,
                        leverage=leverage
                    )
                    logger.critical(
                        f"CRITICAL liquidation warning for {symbol}: "
                        f"{distance:.2f}% from liquidation"
                    )

                elif distance <= self.config.LIQUIDATION_DANGER_THRESHOLD:
                    if self._should_send_alert(alert_key):
                        self.telegram.send_liquidation_warning(
                            chat_id=chat_id,
                            symbol=symbol,
                            side=side,
                            entry_price=entry_price,
                            current_price=mark_price,
                            liquidation_price=liquidation_price,
                            distance_percent=distance,
                            leverage=leverage
                        )
                        self._mark_alert_sent(alert_key)
                        logger.error(
                            f"Liquidation danger for {symbol}: "
                            f"{distance:.2f}% from liquidation"
                        )

                elif distance <= self.config.LIQUIDATION_WARNING_THRESHOLD:
                    if self._should_send_alert(alert_key):
                        self.telegram.send_liquidation_warning(
                            chat_id=chat_id,
                            symbol=symbol,
                            side=side,
                            entry_price=entry_price,
                            current_price=mark_price,
                            liquidation_price=liquidation_price,
                            distance_percent=distance,
                            leverage=leverage
                        )
                        self._mark_alert_sent(alert_key)
                        logger.warning(
                            f"Liquidation warning for {symbol}: "
                            f"{distance:.2f}% from liquidation"
                        )

            except Exception as e:
                logger.error(f"Error checking liquidation for {position.get('symbol')}: {e}")

    async def check_position_concentration(
        self,
        api_key: ApiKey,
        chat_id: str,
        total_balance: float,
        positions: List[Dict]
    ):
        """포지션 집중도 체크"""

        # 포지션 크기 계산
        position_sizes = []
        for position in positions:
            try:
                symbol = position.get('symbol')
                notional = abs(float(position.get('notional', 0)))
                percentage = (notional / total_balance * 100) if total_balance > 0 else 0
                position_sizes.append((symbol, percentage))
            except Exception as e:
                logger.error(f"Error calculating position size: {e}")

        if not position_sizes:
            return

        # 크기별 정렬
        position_sizes.sort(key=lambda x: x[1], reverse=True)

        # 최대 포지션
        largest_symbol, largest_pct = position_sizes[0]

        # 상위 3개 집중도
        top3_pct = sum(pct for _, pct in position_sizes[:3])

        # HHI (Herfindahl-Hirschman Index) 계산
        hhi = sum(pct ** 2 for _, pct in position_sizes)

        # 임계값 체크
        alert_key = f"{api_key.id}_concentration"

        danger_triggered = False
        warning_triggered = False

        if largest_pct > self.config.SINGLE_POSITION_DANGER or top3_pct > self.config.TOP3_CONCENTRATION_DANGER:
            danger_triggered = True
        elif largest_pct > self.config.SINGLE_POSITION_WARNING or top3_pct > self.config.TOP3_CONCENTRATION_WARNING:
            warning_triggered = True

        if danger_triggered or warning_triggered:
            if self._should_send_alert(alert_key):
                self.telegram.send_concentration_warning(
                    chat_id=chat_id,
                    largest_position_symbol=largest_symbol,
                    largest_position_pct=largest_pct,
                    top3_concentration_pct=top3_pct,
                    hhi=hhi,
                    total_positions=len(positions)
                )
                self._mark_alert_sent(alert_key)

                log_level = logger.error if danger_triggered else logger.warning
                log_level(
                    f"Position concentration alert for account {api_key.id}: "
                    f"Largest={largest_pct:.2f}%, Top3={top3_pct:.2f}%, HHI={hhi:.2f}"
                )

    async def check_daily_report(self):
        """일일 리스크 리포트 전송 체크"""

        now = datetime.utcnow()
        current_time = now.time()
        current_date = now.date()

        # 이미 오늘 보냈으면 스킵
        if self.last_daily_report_date == current_date:
            return

        # 리포트 전송 시간 체크 (±5분)
        report_time = self.config.DAILY_REPORT_TIME
        time_diff = abs(
            (current_time.hour * 60 + current_time.minute) -
            (report_time.hour * 60 + report_time.minute)
        )

        if time_diff <= 5:  # 5분 이내
            await self.send_daily_reports()
            self.last_daily_report_date = current_date

    async def send_daily_reports(self):
        """모든 계정에 일일 리포트 전송"""

        db: Session = next(get_db())

        try:
            active_keys = db.query(ApiKey).filter(
                ApiKey.is_active == True
            ).all()

            for api_key in active_keys:
                try:
                    await self.send_account_daily_report(api_key, db)
                except Exception as e:
                    logger.error(f"Error sending daily report for {api_key.id}: {e}")

        finally:
            db.close()

    async def send_account_daily_report(self, api_key: ApiKey, db: Session):
        """개별 계정 일일 리포트"""

        # 거래소 클라이언트 생성
        if api_key.exchange == "binance":
            client = BinanceClient(
                api_key=api_key.api_key,
                api_secret=api_key.api_secret,
                testnet=api_key.testnet
            )
        elif api_key.exchange == "okx":
            client = OKXClient(
                api_key=api_key.api_key,
                api_secret=api_key.api_secret,
                passphrase=api_key.passphrase,
                testnet=api_key.testnet
            )
        else:
            return

        # 텔레그램 채팅 ID
        chat_id = getattr(api_key.user, 'telegram_chat_id', None)
        if not chat_id:
            return

        try:
            # 계정 정보 조회
            balance_info = await client.get_account_balance()
            positions = await client.get_positions()

            total_balance = float(balance_info.get('totalWalletBalance', 0))
            unrealized_profit = float(balance_info.get('totalUnrealizedProfit', 0))

            # 활성 포지션
            active_positions = [p for p in positions if float(p.get('positionAmt', 0)) != 0]

            # 수익/손실 포지션 카운트
            winning_positions = sum(
                1 for p in active_positions
                if float(p.get('unRealizedProfit', 0)) > 0
            )
            losing_positions = len(active_positions) - winning_positions

            # 총 노출
            total_exposure = sum(
                abs(float(p.get('notional', 0)))
                for p in active_positions
            )

            # VaR 추정
            var_amount = total_exposure * 0.05
            var_percentage = (var_amount / total_balance * 100) if total_balance > 0 else 0

            # 최대 낙폭 (간단히 현재 손실로 추정)
            max_drawdown_pct = abs(unrealized_profit / total_balance * 100) if unrealized_profit < 0 else 0

            # 일일 손익 (간단히 미실현 손익으로 추정)
            daily_pnl = unrealized_profit
            daily_pnl_pct = (daily_pnl / total_balance * 100) if total_balance > 0 else 0

            # 리포트 전송
            self.telegram.send_daily_risk_report(
                chat_id=chat_id,
                portfolio_value=total_balance,
                total_exposure=total_exposure,
                var_amount=var_amount,
                var_percentage=var_percentage,
                max_drawdown_pct=max_drawdown_pct,
                total_positions=len(active_positions),
                winning_positions=winning_positions,
                losing_positions=losing_positions,
                daily_pnl=daily_pnl,
                daily_pnl_pct=daily_pnl_pct
            )

            logger.info(f"Daily report sent for account {api_key.id}")

        except Exception as e:
            logger.error(f"Error generating daily report for {api_key.id}: {e}")

    def _should_send_alert(self, alert_key: str) -> bool:
        """알림 전송 여부 체크 (중복 방지)"""

        if alert_key not in self.last_alerts:
            return True

        last_sent = self.last_alerts[alert_key]
        minutes_since = (datetime.utcnow() - last_sent).total_seconds() / 60

        return minutes_since >= self.config.ALERT_COOLDOWN_MINUTES

    def _mark_alert_sent(self, alert_key: str):
        """알림 전송 기록"""
        self.last_alerts[alert_key] = datetime.utcnow()


# 전역 인스턴스
_risk_monitor_instance: Optional[RiskMonitor] = None


async def start_risk_monitor():
    """리스크 모니터 시작 (싱글톤)"""
    global _risk_monitor_instance

    if _risk_monitor_instance is None:
        _risk_monitor_instance = RiskMonitor()

    await _risk_monitor_instance.start()


async def stop_risk_monitor():
    """리스크 모니터 중지"""
    global _risk_monitor_instance

    if _risk_monitor_instance is not None:
        await _risk_monitor_instance.stop()


def get_risk_monitor() -> Optional[RiskMonitor]:
    """현재 리스크 모니터 인스턴스 반환"""
    return _risk_monitor_instance
