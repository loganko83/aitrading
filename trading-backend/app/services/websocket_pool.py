"""
WebSocket Connection Pool Manager

Features:
- 거래소별 연결 풀 관리 (Binance, OKX)
- 연결 재사용 및 멀티플렉싱
- 자동 Health Check 및 정리
- 최대 연결 수 제한
"""

import asyncio
import logging
from typing import Dict, Optional, Set, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from binance import AsyncClient, BinanceSocketManager
import websockets
from websockets.exceptions import WebSocketException

logger = logging.getLogger(__name__)


@dataclass
class WebSocketConnection:
    """WebSocket 연결 정보"""
    connection_id: str
    exchange: str
    ws_client: any  # BinanceSocketManager or websockets.WebSocketClientProtocol
    created_at: datetime
    last_used: datetime
    subscriptions: Set[str] = field(default_factory=set)
    is_healthy: bool = True
    reconnect_count: int = 0

    def add_subscription(self, subscription: str):
        """구독 추가"""
        self.subscriptions.add(subscription)
        self.last_used = datetime.utcnow()

    def remove_subscription(self, subscription: str):
        """구독 제거"""
        self.subscriptions.discard(subscription)
        self.last_used = datetime.utcnow()

    @property
    def is_idle(self) -> bool:
        """유휴 상태 확인 (5분 이상 미사용)"""
        return len(self.subscriptions) == 0 and \
               (datetime.utcnow() - self.last_used) > timedelta(minutes=5)

    @property
    def is_stale(self) -> bool:
        """오래된 연결 확인 (30분 이상)"""
        return (datetime.utcnow() - self.created_at) > timedelta(minutes=30)


class WebSocketConnectionPool:
    """
    WebSocket 연결 풀 관리자

    Features:
    - 거래소별 연결 풀 관리
    - 연결 재사용 (멀티플렉싱)
    - 자동 Health Check
    - 유휴/오래된 연결 자동 정리
    """

    def __init__(
        self,
        max_connections_per_exchange: int = 5,
        health_check_interval: int = 30,
        cleanup_interval: int = 60
    ):
        """
        Args:
            max_connections_per_exchange: 거래소당 최대 연결 수
            health_check_interval: Health check 주기 (초)
            cleanup_interval: 정리 작업 주기 (초)
        """
        self.max_connections_per_exchange = max_connections_per_exchange
        self.health_check_interval = health_check_interval
        self.cleanup_interval = cleanup_interval

        # 연결 풀: {exchange: {connection_id: WebSocketConnection}}
        self.pools: Dict[str, Dict[str, WebSocketConnection]] = {
            "binance": {},
            "okx": {}
        }

        # Binance 클라이언트 캐시
        self.binance_clients: Dict[str, AsyncClient] = {}

        # 백그라운드 작업
        self.health_check_task: Optional[asyncio.Task] = None
        self.cleanup_task: Optional[asyncio.Task] = None

        self._running = False

    async def start(self):
        """연결 풀 시작 (백그라운드 작업 실행)"""
        if self._running:
            logger.warning("WebSocket connection pool already running")
            return

        self._running = True

        # Health check 작업 시작
        self.health_check_task = asyncio.create_task(self._health_check_loop())

        # 정리 작업 시작
        self.cleanup_task = asyncio.create_task(self._cleanup_loop())

        logger.info("WebSocket connection pool started")

    async def stop(self):
        """연결 풀 중지 (모든 연결 종료)"""
        self._running = False

        # 백그라운드 작업 취소
        if self.health_check_task:
            self.health_check_task.cancel()
            try:
                await self.health_check_task
            except asyncio.CancelledError:
                pass

        if self.cleanup_task:
            self.cleanup_task.cancel()
            try:
                await self.cleanup_task
            except asyncio.CancelledError:
                pass

        # 모든 연결 종료
        for exchange in self.pools:
            await self._close_all_connections(exchange)

        # Binance 클라이언트 정리
        for client in self.binance_clients.values():
            await client.close_connection()

        self.binance_clients.clear()

        logger.info("WebSocket connection pool stopped")

    async def get_connection(
        self,
        exchange: str,
        api_key: str = "",
        api_secret: str = ""
    ) -> Optional[WebSocketConnection]:
        """
        연결 가져오기 (재사용 또는 새로 생성)

        Args:
            exchange: 거래소 (binance, okx)
            api_key: API 키 (Binance만)
            api_secret: API Secret (Binance만)

        Returns:
            WebSocketConnection 또는 None
        """
        exchange = exchange.lower()

        if exchange not in self.pools:
            logger.error(f"Unsupported exchange: {exchange}")
            return None

        pool = self.pools[exchange]

        # 1. 재사용 가능한 연결 찾기 (건강하고 구독 < 10개)
        for conn in pool.values():
            if conn.is_healthy and len(conn.subscriptions) < 10:
                logger.debug(f"Reusing existing connection: {conn.connection_id}")
                return conn

        # 2. 최대 연결 수 확인
        if len(pool) >= self.max_connections_per_exchange:
            logger.warning(f"Max connections reached for {exchange}: {len(pool)}")
            # 가장 구독이 적은 연결 반환
            return min(pool.values(), key=lambda c: len(c.subscriptions))

        # 3. 새 연결 생성
        return await self._create_connection(exchange, api_key, api_secret)

    async def _create_connection(
        self,
        exchange: str,
        api_key: str,
        api_secret: str
    ) -> Optional[WebSocketConnection]:
        """새 WebSocket 연결 생성"""
        connection_id = f"{exchange}_{len(self.pools[exchange])}"

        try:
            if exchange == "binance":
                # Binance 클라이언트 생성 또는 재사용
                client_key = f"{api_key}_{api_secret}"

                if client_key not in self.binance_clients:
                    client = await AsyncClient.create(
                        api_key=api_key,
                        api_secret=api_secret
                    )
                    self.binance_clients[client_key] = client
                else:
                    client = self.binance_clients[client_key]

                ws_client = BinanceSocketManager(client)

            elif exchange == "okx":
                # OKX는 구독 시점에 연결 생성 (여기서는 플레이스홀더)
                ws_client = None

            else:
                logger.error(f"Unsupported exchange: {exchange}")
                return None

            # 연결 객체 생성
            connection = WebSocketConnection(
                connection_id=connection_id,
                exchange=exchange,
                ws_client=ws_client,
                created_at=datetime.utcnow(),
                last_used=datetime.utcnow()
            )

            # 풀에 추가
            self.pools[exchange][connection_id] = connection

            logger.info(f"Created new connection: {connection_id}")

            return connection

        except Exception as e:
            logger.error(f"Failed to create connection for {exchange}: {e}")
            return None

    async def release_connection(
        self,
        exchange: str,
        connection_id: str,
        subscription: str
    ):
        """
        구독 해제 및 연결 반환

        Args:
            exchange: 거래소
            connection_id: 연결 ID
            subscription: 구독 키 (예: "ticker_BTCUSDT")
        """
        exchange = exchange.lower()

        if exchange not in self.pools:
            return

        pool = self.pools[exchange]

        if connection_id not in pool:
            return

        connection = pool[connection_id]
        connection.remove_subscription(subscription)

        logger.debug(
            f"Released subscription {subscription} from {connection_id}. "
            f"Remaining: {len(connection.subscriptions)}"
        )

    async def _health_check_loop(self):
        """주기적 Health Check"""
        while self._running:
            try:
                await asyncio.sleep(self.health_check_interval)

                for exchange, pool in self.pools.items():
                    for conn_id, conn in pool.items():
                        # Binance 연결 상태 확인
                        if exchange == "binance":
                            try:
                                # Binance 클라이언트 ping
                                client_key = list(self.binance_clients.keys())[0]
                                client = self.binance_clients.get(client_key)

                                if client:
                                    await client.ping()
                                    conn.is_healthy = True
                                else:
                                    conn.is_healthy = False

                            except Exception as e:
                                logger.error(f"Health check failed for {conn_id}: {e}")
                                conn.is_healthy = False

                logger.debug("Health check completed")

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health check error: {e}")

    async def _cleanup_loop(self):
        """주기적 정리 작업 (유휴/오래된 연결 제거)"""
        while self._running:
            try:
                await asyncio.sleep(self.cleanup_interval)

                for exchange, pool in self.pools.items():
                    # 정리 대상 연결 찾기
                    to_remove = []

                    for conn_id, conn in pool.items():
                        if conn.is_idle or conn.is_stale or not conn.is_healthy:
                            to_remove.append(conn_id)

                    # 연결 종료 및 제거
                    for conn_id in to_remove:
                        await self._close_connection(exchange, conn_id)

                    if to_remove:
                        logger.info(f"Cleaned up {len(to_remove)} connections from {exchange}")

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cleanup error: {e}")

    async def _close_connection(self, exchange: str, connection_id: str):
        """단일 연결 종료"""
        pool = self.pools.get(exchange)

        if not pool or connection_id not in pool:
            return

        connection = pool[connection_id]

        try:
            if exchange == "binance":
                # Binance 소켓 정리 (구독 취소)
                # BinanceSocketManager는 자동으로 정리됨
                pass

            elif exchange == "okx":
                # OKX WebSocket 연결 종료
                if connection.ws_client:
                    await connection.ws_client.close()

        except Exception as e:
            logger.error(f"Error closing connection {connection_id}: {e}")

        finally:
            del pool[connection_id]
            logger.info(f"Closed connection: {connection_id}")

    async def _close_all_connections(self, exchange: str):
        """거래소의 모든 연결 종료"""
        pool = self.pools.get(exchange)

        if not pool:
            return

        connection_ids = list(pool.keys())

        for conn_id in connection_ids:
            await self._close_connection(exchange, conn_id)

        logger.info(f"Closed all connections for {exchange}")

    def get_pool_stats(self) -> Dict[str, any]:
        """연결 풀 통계"""
        stats = {}

        for exchange, pool in self.pools.items():
            total_subscriptions = sum(len(conn.subscriptions) for conn in pool.values())
            healthy_count = sum(1 for conn in pool.values() if conn.is_healthy)

            stats[exchange] = {
                "total_connections": len(pool),
                "healthy_connections": healthy_count,
                "total_subscriptions": total_subscriptions,
                "max_connections": self.max_connections_per_exchange,
                "utilization_pct": round(len(pool) / self.max_connections_per_exchange * 100, 2)
            }

        return stats


# 전역 싱글톤 인스턴스
websocket_pool = WebSocketConnectionPool(
    max_connections_per_exchange=5,
    health_check_interval=30,
    cleanup_interval=60
)
