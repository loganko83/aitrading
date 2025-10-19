"""
WebSocket 자동 재연결 시스템

Features:
- Exponential Backoff (1s → 2s → 4s → ... → 30s)
- 최대 재시도 횟수 제한
- 구독 상태 복원
- 연결 실패 알림
"""

import asyncio
import logging
from typing import Optional, Callable, Dict, Any
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class ReconnectState(str, Enum):
    """재연결 상태"""
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    RECONNECTING = "reconnecting"
    FAILED = "failed"


@dataclass
class ReconnectConfig:
    """재연결 설정"""
    max_retries: int = 10
    initial_delay: float = 1.0
    max_delay: float = 30.0
    backoff_factor: float = 2.0
    jitter: float = 0.1  # 재시도 지연에 랜덤 지터 추가


@dataclass
class ReconnectContext:
    """재연결 컨텍스트"""
    connection_id: str
    exchange: str
    subscription_key: str
    retry_count: int = 0
    state: ReconnectState = ReconnectState.CONNECTED
    last_error: Optional[str] = None
    last_attempt: Optional[datetime] = None
    subscriptions_to_restore: Dict[str, Any] = None

    def __post_init__(self):
        if self.subscriptions_to_restore is None:
            self.subscriptions_to_restore = {}


class WebSocketReconnector:
    """
    WebSocket 자동 재연결 관리자

    Features:
    - Exponential backoff with jitter
    - 재연결 시 구독 상태 복원
    - 최대 재시도 제한
    - 실패 알림
    """

    def __init__(self, config: Optional[ReconnectConfig] = None):
        """
        Args:
            config: 재연결 설정 (기본값 사용 시 None)
        """
        self.config = config or ReconnectConfig()

        # 재연결 컨텍스트: {connection_id: ReconnectContext}
        self.contexts: Dict[str, ReconnectContext] = {}

        # 재연결 작업: {connection_id: asyncio.Task}
        self.reconnect_tasks: Dict[str, asyncio.Task] = {}

    async def handle_disconnect(
        self,
        connection_id: str,
        exchange: str,
        subscription_key: str,
        error: Exception,
        reconnect_callback: Callable,
        subscriptions_to_restore: Optional[Dict[str, Any]] = None
    ):
        """
        연결 끊김 처리 및 재연결 시작

        Args:
            connection_id: 연결 ID
            exchange: 거래소
            subscription_key: 구독 키
            error: 발생한 에러
            reconnect_callback: 재연결 콜백 함수
            subscriptions_to_restore: 복원할 구독 목록
        """
        # 컨텍스트 생성 또는 업데이트
        if connection_id not in self.contexts:
            context = ReconnectContext(
                connection_id=connection_id,
                exchange=exchange,
                subscription_key=subscription_key,
                subscriptions_to_restore=subscriptions_to_restore or {}
            )
            self.contexts[connection_id] = context
        else:
            context = self.contexts[connection_id]

        context.state = ReconnectState.DISCONNECTED
        context.last_error = str(error)

        logger.warning(
            f"WebSocket disconnected: {connection_id} ({subscription_key}). "
            f"Error: {error}. Starting reconnection..."
        )

        # 재연결 작업 시작 (이미 실행 중이면 스킵)
        if connection_id not in self.reconnect_tasks or self.reconnect_tasks[connection_id].done():
            task = asyncio.create_task(
                self._reconnect_loop(context, reconnect_callback)
            )
            self.reconnect_tasks[connection_id] = task

    async def _reconnect_loop(
        self,
        context: ReconnectContext,
        reconnect_callback: Callable
    ):
        """재연결 루프 (Exponential Backoff)"""
        context.state = ReconnectState.RECONNECTING

        while context.retry_count < self.config.max_retries:
            # 재시도 지연 계산 (Exponential Backoff)
            delay = self._calculate_delay(context.retry_count)

            logger.info(
                f"Reconnecting {context.connection_id} in {delay:.1f}s "
                f"(attempt {context.retry_count + 1}/{self.config.max_retries})"
            )

            await asyncio.sleep(delay)

            context.retry_count += 1
            context.last_attempt = datetime.utcnow()

            try:
                # 재연결 시도
                success = await reconnect_callback(
                    context.connection_id,
                    context.exchange,
                    context.subscription_key,
                    context.subscriptions_to_restore
                )

                if success:
                    # 재연결 성공
                    logger.info(f"✅ Reconnected successfully: {context.connection_id}")

                    context.state = ReconnectState.CONNECTED
                    context.retry_count = 0
                    context.last_error = None

                    # 컨텍스트 정리
                    if context.connection_id in self.contexts:
                        del self.contexts[context.connection_id]

                    return

                else:
                    # 재연결 실패 (다음 시도 계속)
                    logger.warning(
                        f"Reconnection attempt failed: {context.connection_id}. "
                        f"Retrying..."
                    )

            except Exception as e:
                # 재연결 중 에러
                logger.error(
                    f"Error during reconnection {context.connection_id}: {e}. "
                    f"Retrying..."
                )
                context.last_error = str(e)

        # 최대 재시도 초과
        logger.error(
            f"❌ Max retries exceeded for {context.connection_id}. "
            f"Reconnection failed."
        )

        context.state = ReconnectState.FAILED

        # 실패 알림 (TODO: Telegram 알림 연동)
        await self._notify_reconnect_failure(context)

    def _calculate_delay(self, retry_count: int) -> float:
        """
        재시도 지연 계산 (Exponential Backoff + Jitter)

        Formula:
            delay = min(initial_delay * (backoff_factor ^ retry_count), max_delay)
            delay = delay * (1 + random(-jitter, +jitter))
        """
        import random

        delay = self.config.initial_delay * (self.config.backoff_factor ** retry_count)
        delay = min(delay, self.config.max_delay)

        # Jitter 추가 (randomization to prevent thundering herd)
        jitter = random.uniform(-self.config.jitter, self.config.jitter)
        delay = delay * (1 + jitter)

        return delay

    async def _notify_reconnect_failure(self, context: ReconnectContext):
        """재연결 실패 알림"""
        # TODO: Telegram 알림 연동
        logger.critical(
            f"🚨 WebSocket reconnection failed: {context.connection_id}\n"
            f"Exchange: {context.exchange}\n"
            f"Subscription: {context.subscription_key}\n"
            f"Retry count: {context.retry_count}\n"
            f"Last error: {context.last_error}"
        )

    def cancel_reconnect(self, connection_id: str):
        """재연결 취소"""
        if connection_id in self.reconnect_tasks:
            task = self.reconnect_tasks[connection_id]

            if not task.done():
                task.cancel()
                logger.info(f"Cancelled reconnection for {connection_id}")

            del self.reconnect_tasks[connection_id]

        if connection_id in self.contexts:
            del self.contexts[connection_id]

    def get_reconnect_stats(self) -> Dict[str, Any]:
        """재연결 통계"""
        active_reconnects = sum(
            1 for task in self.reconnect_tasks.values() if not task.done()
        )

        states = {}
        for state in ReconnectState:
            states[state.value] = sum(
                1 for ctx in self.contexts.values() if ctx.state == state
            )

        return {
            "active_reconnects": active_reconnects,
            "total_contexts": len(self.contexts),
            "states": states,
            "max_retries": self.config.max_retries,
            "max_delay": self.config.max_delay
        }


# 전역 싱글톤 인스턴스
websocket_reconnector = WebSocketReconnector(
    config=ReconnectConfig(
        max_retries=10,
        initial_delay=1.0,
        max_delay=30.0,
        backoff_factor=2.0,
        jitter=0.1
    )
)
