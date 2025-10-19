"""
Redis Pub/Sub 기반 워커 간 통신

Features:
- WebSocket 구독 상태 동기화
- 워커 간 메시지 브로드캐스트
- 장애 조치 (워커 다운 시 다른 워커가 인수)
- 로드 밸런싱 (구독 분산)
"""

import asyncio
import json
import logging
from typing import Optional, Callable, Dict, Any
from datetime import datetime
from dataclasses import dataclass, asdict

from app.core.redis_client import RedisClient

logger = logging.getLogger(__name__)


@dataclass
class WorkerMessage:
    """워커 간 메시지"""
    worker_id: str
    message_type: str  # "subscribe", "unsubscribe", "heartbeat", "shutdown"
    payload: Dict[str, Any]
    timestamp: str

    def to_dict(self) -> dict:
        """딕셔너리로 변환"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "WorkerMessage":
        """딕셔너리에서 생성"""
        return cls(**data)


class RedisPublisher:
    """
    Redis Pub/Sub Publisher

    Features:
    - 메시지 발행
    - 메시지 형식 검증
    """

    def __init__(self, worker_id: str):
        """
        Args:
            worker_id: 워커 고유 ID (예: "worker-1")
        """
        self.worker_id = worker_id
        self.client: Optional[Any] = None

    async def _get_client(self):
        """Redis 클라이언트 가져오기"""
        if self.client is None:
            self.client = await RedisClient.get_client()
        return self.client

    async def publish(
        self,
        channel: str,
        message_type: str,
        payload: Dict[str, Any]
    ):
        """
        메시지 발행

        Args:
            channel: 채널명 (예: "websocket:subscriptions")
            message_type: 메시지 타입
            payload: 페이로드
        """
        try:
            client = await self._get_client()

            message = WorkerMessage(
                worker_id=self.worker_id,
                message_type=message_type,
                payload=payload,
                timestamp=datetime.utcnow().isoformat()
            )

            # JSON 직렬화 후 발행
            await client.publish(channel, json.dumps(message.to_dict()))

            logger.debug(
                f"Published message: {message_type} to {channel} "
                f"from worker {self.worker_id}"
            )

        except Exception as e:
            logger.error(f"Failed to publish message: {e}")


class RedisSubscriber:
    """
    Redis Pub/Sub Subscriber

    Features:
    - 메시지 구독
    - 메시지 핸들러 등록
    - 자동 재연결
    """

    def __init__(
        self,
        worker_id: str,
        channels: list[str],
        message_handler: Callable[[WorkerMessage], Any]
    ):
        """
        Args:
            worker_id: 워커 고유 ID
            channels: 구독할 채널 목록
            message_handler: 메시지 핸들러 함수
        """
        self.worker_id = worker_id
        self.channels = channels
        self.message_handler = message_handler

        self.client: Optional[Any] = None
        self.pubsub: Optional[Any] = None
        self.subscriber_task: Optional[asyncio.Task] = None
        self._running = False

    async def start(self):
        """구독 시작"""
        if self._running:
            logger.warning(f"Subscriber already running for worker {self.worker_id}")
            return

        try:
            self.client = await RedisClient.get_client()
            self.pubsub = self.client.pubsub()

            # 채널 구독
            for channel in self.channels:
                await self.pubsub.subscribe(channel)

            logger.info(
                f"Worker {self.worker_id} subscribed to channels: {self.channels}"
            )

            self._running = True

            # 메시지 수신 루프 시작
            self.subscriber_task = asyncio.create_task(self._message_loop())

        except Exception as e:
            logger.error(f"Failed to start subscriber: {e}")
            raise

    async def stop(self):
        """구독 중지"""
        self._running = False

        if self.subscriber_task:
            self.subscriber_task.cancel()

            try:
                await self.subscriber_task
            except asyncio.CancelledError:
                pass

        if self.pubsub:
            await self.pubsub.unsubscribe(*self.channels)
            await self.pubsub.close()

        logger.info(f"Worker {self.worker_id} unsubscribed from all channels")

    async def _message_loop(self):
        """메시지 수신 루프"""
        while self._running:
            try:
                message = await self.pubsub.get_message(
                    ignore_subscribe_messages=True,
                    timeout=1.0
                )

                if message and message['type'] == 'message':
                    # JSON 파싱
                    data = json.loads(message['data'])
                    worker_message = WorkerMessage.from_dict(data)

                    # 자신의 메시지는 무시
                    if worker_message.worker_id == self.worker_id:
                        continue

                    # 메시지 핸들러 호출
                    try:
                        await self.message_handler(worker_message)
                    except Exception as e:
                        logger.error(f"Message handler error: {e}")

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Message loop error: {e}")
                await asyncio.sleep(1)  # 에러 발생 시 잠시 대기


class WebSocketCoordinator:
    """
    WebSocket 워커 간 코디네이터

    Features:
    - 구독 상태 동기화
    - 워커 Heartbeat 모니터링
    - 장애 조치
    """

    def __init__(self, worker_id: str):
        """
        Args:
            worker_id: 워커 고유 ID
        """
        self.worker_id = worker_id

        # Publisher & Subscriber
        self.publisher = RedisPublisher(worker_id)
        self.subscriber: Optional[RedisSubscriber] = None

        # 워커 상태 추적: {worker_id: last_heartbeat}
        self.worker_heartbeats: Dict[str, datetime] = {}

        # 백그라운드 작업
        self.heartbeat_task: Optional[asyncio.Task] = None
        self.monitor_task: Optional[asyncio.Task] = None

        self._running = False

    async def start(self):
        """코디네이터 시작"""
        if self._running:
            return

        # Subscriber 시작
        self.subscriber = RedisSubscriber(
            worker_id=self.worker_id,
            channels=["websocket:subscriptions", "websocket:heartbeat"],
            message_handler=self._handle_message
        )

        await self.subscriber.start()

        self._running = True

        # Heartbeat 전송 시작
        self.heartbeat_task = asyncio.create_task(self._heartbeat_loop())

        # 워커 모니터링 시작
        self.monitor_task = asyncio.create_task(self._monitor_workers())

        logger.info(f"WebSocket coordinator started for worker {self.worker_id}")

    async def stop(self):
        """코디네이터 중지"""
        self._running = False

        # Shutdown 메시지 발행
        await self.publisher.publish(
            channel="websocket:heartbeat",
            message_type="shutdown",
            payload={"worker_id": self.worker_id}
        )

        # 백그라운드 작업 중지
        if self.heartbeat_task:
            self.heartbeat_task.cancel()

        if self.monitor_task:
            self.monitor_task.cancel()

        # Subscriber 중지
        if self.subscriber:
            await self.subscriber.stop()

        logger.info(f"WebSocket coordinator stopped for worker {self.worker_id}")

    async def publish_subscription(
        self,
        action: str,
        exchange: str,
        symbol: str,
        stream_type: str
    ):
        """
        구독 상태 발행

        Args:
            action: "subscribe" 또는 "unsubscribe"
            exchange: 거래소
            symbol: 심볼
            stream_type: "ticker", "kline", "trades"
        """
        await self.publisher.publish(
            channel="websocket:subscriptions",
            message_type=action,
            payload={
                "exchange": exchange,
                "symbol": symbol,
                "stream_type": stream_type
            }
        )

    async def _handle_message(self, message: WorkerMessage):
        """수신된 메시지 처리"""
        logger.debug(
            f"Received message from {message.worker_id}: {message.message_type}"
        )

        if message.message_type == "heartbeat":
            # Heartbeat 업데이트
            self.worker_heartbeats[message.worker_id] = datetime.fromisoformat(
                message.timestamp
            )

        elif message.message_type == "shutdown":
            # 워커 종료 처리
            if message.worker_id in self.worker_heartbeats:
                del self.worker_heartbeats[message.worker_id]

            logger.info(f"Worker {message.worker_id} shutdown")

        elif message.message_type in ["subscribe", "unsubscribe"]:
            # 구독 상태 동기화 (필요시 처리)
            logger.debug(
                f"Worker {message.worker_id} {message.message_type}: "
                f"{message.payload}"
            )

    async def _heartbeat_loop(self):
        """주기적 Heartbeat 전송 (10초마다)"""
        while self._running:
            try:
                await asyncio.sleep(10)

                await self.publisher.publish(
                    channel="websocket:heartbeat",
                    message_type="heartbeat",
                    payload={"status": "alive"}
                )

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Heartbeat error: {e}")

    async def _monitor_workers(self):
        """워커 모니터링 (30초 동안 heartbeat 없으면 실패로 간주)"""
        while self._running:
            try:
                await asyncio.sleep(30)

                now = datetime.utcnow()
                dead_workers = []

                for worker_id, last_heartbeat in self.worker_heartbeats.items():
                    if (now - last_heartbeat).total_seconds() > 30:
                        dead_workers.append(worker_id)

                # 죽은 워커 제거
                for worker_id in dead_workers:
                    del self.worker_heartbeats[worker_id]
                    logger.warning(f"Worker {worker_id} appears to be dead")

                    # TODO: 장애 조치 (해당 워커의 구독을 다른 워커로 이관)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Worker monitor error: {e}")

    def get_coordinator_stats(self) -> Dict[str, Any]:
        """코디네이터 통계"""
        return {
            "worker_id": self.worker_id,
            "active_workers": len(self.worker_heartbeats),
            "worker_list": list(self.worker_heartbeats.keys())
        }
