import asyncio
import json
import websockets
from typing import Dict, Set, Callable, List, Optional
from fastapi import WebSocket
from binance import AsyncClient, BinanceSocketManager
import logging
import uuid

from app.services.websocket_pool import websocket_pool, WebSocketConnection
from app.services.websocket_reconnect import websocket_reconnector
from app.core.redis_pubsub import WebSocketCoordinator

logger = logging.getLogger(__name__)


class WebSocketManager:
    """
    WebSocket manager for real-time market data streaming

    Features (Enhanced):
    - 연결 풀 관리 (최대 5개/거래소)
    - 연결 재사용 및 멀티플렉싱
    - 자동 재연결 (Exponential Backoff)
    - 워커 간 통신 (Redis Pub/Sub)
    - Health Check 및 모니터링
    """

    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

        # Legacy fields (호환성 유지)
        self.binance_client: AsyncClient = None
        self.binance_socket_manager: BinanceSocketManager = None
        self.okx_connections: Dict[str, websockets.WebSocketClientProtocol] = {}
        self.active_streams: Dict[str, asyncio.Task] = {}
        self.subscribed_symbols: Set[str] = set()

        # 워커 ID 생성
        self.worker_id = f"worker-{uuid.uuid4().hex[:8]}"

        # 코디네이터 (워커 간 통신)
        self.coordinator: Optional[WebSocketCoordinator] = None

        # 구독 → 연결 매핑: {subscription_key: connection_id}
        self.subscription_mapping: Dict[str, str] = {}

        # 초기화 완료 플래그
        self._initialized = False

    async def connect(self, websocket: WebSocket):
        """Accept and register a new WebSocket connection"""
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"New WebSocket connection. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection"""
        self.active_connections.discard(websocket)
        logger.info(f"WebSocket disconnected. Total: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients"""
        if not self.active_connections:
            return

        dead_connections = set()

        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error sending to client: {e}")
                dead_connections.add(connection)

        # Clean up dead connections
        for connection in dead_connections:
            self.disconnect(connection)

    async def initialize_binance_client(self, api_key: str, api_secret: str):
        """Initialize Binance async client for WebSocket streaming"""
        try:
            self.binance_client = await AsyncClient.create(
                api_key=api_key,
                api_secret=api_secret
            )
            self.binance_socket_manager = BinanceSocketManager(self.binance_client)
            logger.info("Binance WebSocket client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Binance client: {e}")
            raise

    async def subscribe_ticker(self, symbol: str, api_key: str = "", api_secret: str = ""):
        """
        Subscribe to ticker updates for a symbol (연결 풀 기반)

        Streams: price, 24h volume, 24h high/low, price change %
        """
        subscription_key = f"ticker_{symbol}"

        if subscription_key in self.subscription_mapping:
            logger.info(f"Already subscribed to {symbol}")
            return

        try:
            # 연결 풀에서 연결 가져오기 (재사용 또는 새로 생성)
            connection = await websocket_pool.get_connection(
                exchange="binance",
                api_key=api_key,
                api_secret=api_secret
            )

            if not connection:
                raise Exception("Failed to get connection from pool")

            # 구독 등록
            connection.add_subscription(subscription_key)
            self.subscription_mapping[subscription_key] = connection.connection_id

            # Create ticker stream
            ticker_socket = connection.ws_client.symbol_ticker_socket(symbol)

            # Start streaming task with reconnection support
            task = asyncio.create_task(
                self._stream_ticker_with_reconnect(
                    ticker_socket,
                    symbol,
                    connection.connection_id,
                    api_key,
                    api_secret
                )
            )

            self.active_streams[subscription_key] = task
            self.subscribed_symbols.add(symbol)

            # 워커 간 동기화 (Redis Pub/Sub)
            if self.coordinator:
                await self.coordinator.publish_subscription(
                    action="subscribe",
                    exchange="binance",
                    symbol=symbol,
                    stream_type="ticker"
                )

            logger.info(
                f"✅ Subscribed to ticker {symbol} on connection {connection.connection_id}"
            )

        except Exception as e:
            logger.error(f"Error subscribing to ticker {symbol}: {e}")
            raise

    async def _stream_ticker(self, ticker_socket, symbol: str):
        """Internal method to stream ticker data (레거시 - 호환성 유지)"""
        async with ticker_socket as stream:
            while True:
                try:
                    msg = await stream.recv()

                    # Parse Binance ticker data
                    ticker_data = {
                        "type": "ticker",
                        "symbol": msg['s'],
                        "price": float(msg['c']),
                        "priceChange": float(msg['p']),
                        "priceChangePercent": float(msg['P']),
                        "volume": float(msg['v']),
                        "high": float(msg['h']),
                        "low": float(msg['l']),
                        "timestamp": msg['E']
                    }

                    # Broadcast to all connected clients
                    await self.broadcast(ticker_data)

                except Exception as e:
                    logger.error(f"Error in ticker stream {symbol}: {e}")
                    break

    async def _stream_ticker_with_reconnect(
        self,
        ticker_socket,
        symbol: str,
        connection_id: str,
        api_key: str,
        api_secret: str
    ):
        """재연결 지원 티커 스트리밍"""
        subscription_key = f"ticker_{symbol}"

        async with ticker_socket as stream:
            while True:
                try:
                    msg = await stream.recv()

                    # Parse Binance ticker data
                    ticker_data = {
                        "type": "ticker",
                        "symbol": msg['s'],
                        "price": float(msg['c']),
                        "priceChange": float(msg['p']),
                        "priceChangePercent": float(msg['P']),
                        "volume": float(msg['v']),
                        "high": float(msg['h']),
                        "low": float(msg['l']),
                        "timestamp": msg['E']
                    }

                    # Broadcast to all connected clients
                    await self.broadcast(ticker_data)

                except Exception as e:
                    logger.error(f"Ticker stream error for {symbol}: {e}")

                    # 자동 재연결 시작
                    await websocket_reconnector.handle_disconnect(
                        connection_id=connection_id,
                        exchange="binance",
                        subscription_key=subscription_key,
                        error=e,
                        reconnect_callback=self._reconnect_ticker,
                        subscriptions_to_restore={
                            "symbol": symbol,
                            "api_key": api_key,
                            "api_secret": api_secret
                        }
                    )

                    break

    async def _reconnect_ticker(
        self,
        connection_id: str,
        exchange: str,
        subscription_key: str,
        subscriptions_to_restore: dict
    ) -> bool:
        """티커 재연결 콜백"""
        try:
            symbol = subscriptions_to_restore["symbol"]
            api_key = subscriptions_to_restore["api_key"]
            api_secret = subscriptions_to_restore["api_secret"]

            logger.info(f"Reconnecting ticker stream for {symbol}...")

            # 기존 구독 해제
            await self.unsubscribe(subscription_key)

            # 재구독
            await self.subscribe_ticker(symbol, api_key, api_secret)

            return True

        except Exception as e:
            logger.error(f"Reconnection failed for {subscription_key}: {e}")
            return False

    async def subscribe_kline(self, symbol: str, interval: str = "1m"):
        """
        Subscribe to kline (candlestick) updates

        Args:
            symbol: Trading pair (e.g., BTCUSDT)
            interval: Kline interval (1m, 5m, 15m, 1h, 4h, 1d)
        """
        stream_key = f"kline_{symbol}_{interval}"

        if stream_key in self.active_streams:
            logger.info(f"Already subscribed to {stream_key}")
            return

        try:
            # Create kline stream
            kline_socket = self.binance_socket_manager.kline_socket(
                symbol=symbol,
                interval=interval
            )

            # Start streaming task
            task = asyncio.create_task(
                self._stream_kline(kline_socket, symbol, interval)
            )

            self.active_streams[stream_key] = task

            logger.info(f"Subscribed to kline stream {stream_key}")

        except Exception as e:
            logger.error(f"Error subscribing to kline {stream_key}: {e}")
            raise

    async def _stream_kline(self, kline_socket, symbol: str, interval: str):
        """Internal method to stream kline data"""
        async with kline_socket as stream:
            while True:
                try:
                    msg = await stream.recv()

                    kline = msg['k']

                    # Parse kline data
                    kline_data = {
                        "type": "kline",
                        "symbol": kline['s'],
                        "interval": kline['i'],
                        "openTime": kline['t'],
                        "closeTime": kline['T'],
                        "open": float(kline['o']),
                        "high": float(kline['h']),
                        "low": float(kline['l']),
                        "close": float(kline['c']),
                        "volume": float(kline['v']),
                        "isClosed": kline['x']
                    }

                    # Broadcast to all connected clients
                    await self.broadcast(kline_data)

                except Exception as e:
                    logger.error(f"Error in kline stream {symbol}_{interval}: {e}")
                    break

    async def subscribe_trades(self, symbol: str):
        """
        Subscribe to trade updates (order book executions)

        Real-time trade data: price, quantity, buyer/seller info
        """
        stream_key = f"trades_{symbol}"

        if stream_key in self.active_streams:
            logger.info(f"Already subscribed to {stream_key}")
            return

        try:
            # Create trade stream
            trade_socket = self.binance_socket_manager.trade_socket(symbol)

            # Start streaming task
            task = asyncio.create_task(
                self._stream_trades(trade_socket, symbol)
            )

            self.active_streams[stream_key] = task

            logger.info(f"Subscribed to trade stream {stream_key}")

        except Exception as e:
            logger.error(f"Error subscribing to trades {stream_key}: {e}")
            raise

    async def _stream_trades(self, trade_socket, symbol: str):
        """Internal method to stream trade data"""
        async with trade_socket as stream:
            while True:
                try:
                    msg = await stream.recv()

                    # Parse trade data
                    trade_data = {
                        "type": "trade",
                        "symbol": msg['s'],
                        "price": float(msg['p']),
                        "quantity": float(msg['q']),
                        "time": msg['T'],
                        "isBuyerMaker": msg['m']
                    }

                    # Broadcast to all connected clients
                    await self.broadcast(trade_data)

                except Exception as e:
                    logger.error(f"Error in trade stream {symbol}: {e}")
                    break

    async def unsubscribe(self, stream_key: str):
        """Unsubscribe from a specific stream"""
        if stream_key in self.active_streams:
            task = self.active_streams[stream_key]
            task.cancel()

            try:
                await task
            except asyncio.CancelledError:
                pass

            del self.active_streams[stream_key]

            # Remove from subscribed symbols if ticker stream
            if stream_key.startswith("ticker_"):
                symbol = stream_key.replace("ticker_", "")
                self.subscribed_symbols.discard(symbol)

            logger.info(f"Unsubscribed from {stream_key}")

    async def subscribe_okx_ticker(self, symbol: str):
        """
        Subscribe to OKX ticker updates

        Args:
            symbol: Trading pair in OKX format (e.g., BTC-USDT-SWAP)
        """
        stream_key = f"okx_ticker_{symbol}"

        if stream_key in self.active_streams:
            logger.info(f"Already subscribed to {stream_key}")
            return

        try:
            # OKX WebSocket URL
            ws_url = "wss://ws.okx.com:8443/ws/v5/public"

            # Start streaming task
            task = asyncio.create_task(
                self._stream_okx_ticker(ws_url, symbol)
            )

            self.active_streams[stream_key] = task
            self.subscribed_symbols.add(symbol)

            logger.info(f"Subscribed to OKX ticker stream for {symbol}")

        except Exception as e:
            logger.error(f"Error subscribing to OKX ticker {symbol}: {e}")
            raise

    async def _stream_okx_ticker(self, ws_url: str, symbol: str):
        """Internal method to stream OKX ticker data"""
        try:
            async with websockets.connect(ws_url) as ws:
                # Subscribe to ticker channel
                subscribe_msg = {
                    "op": "subscribe",
                    "args": [
                        {
                            "channel": "tickers",
                            "instId": symbol
                        }
                    ]
                }

                await ws.send(json.dumps(subscribe_msg))
                logger.info(f"Sent OKX subscription for {symbol}")

                while True:
                    try:
                        msg = await ws.recv()
                        data = json.loads(msg)

                        # Check if it's ticker data
                        if "data" in data:
                            for ticker in data["data"]:
                                ticker_data = {
                                    "type": "ticker",
                                    "exchange": "okx",
                                    "symbol": ticker["instId"],
                                    "price": float(ticker["last"]),
                                    "priceChange": float(ticker["last"]) - float(ticker["open24h"]),
                                    "priceChangePercent": ((float(ticker["last"]) - float(ticker["open24h"])) / float(ticker["open24h"]) * 100) if float(ticker["open24h"]) > 0 else 0,
                                    "volume": float(ticker["vol24h"]),
                                    "high": float(ticker["high24h"]),
                                    "low": float(ticker["low24h"]),
                                    "timestamp": int(ticker["ts"])
                                }

                                # Broadcast to all connected clients
                                await self.broadcast(ticker_data)

                    except Exception as e:
                        logger.error(f"Error in OKX ticker stream {symbol}: {e}")
                        break

        except Exception as e:
            logger.error(f"OKX WebSocket connection error for {symbol}: {e}")

    async def subscribe_multi_symbols(self, exchange: str, symbols: List[str]):
        """
        Subscribe to multiple symbols at once

        Args:
            exchange: 'binance' or 'okx'
            symbols: List of symbols to subscribe
        """
        for symbol in symbols:
            try:
                if exchange.lower() == "binance":
                    await self.subscribe_ticker(symbol)
                elif exchange.lower() == "okx":
                    await self.subscribe_okx_ticker(symbol)
                else:
                    logger.warning(f"Unsupported exchange: {exchange}")

                # Small delay to avoid rate limiting
                await asyncio.sleep(0.1)

            except Exception as e:
                logger.error(f"Error subscribing to {symbol} on {exchange}: {e}")

        logger.info(f"Subscribed to {len(symbols)} symbols on {exchange}")

    async def unsubscribe_all(self):
        """Unsubscribe from all active streams"""
        for stream_key in list(self.active_streams.keys()):
            await self.unsubscribe(stream_key)

        logger.info("Unsubscribed from all streams")

    async def close(self):
        """Close all connections and cleanup (연결 풀, 재연결, 코디네이터 통합)"""
        logger.info("Closing WebSocket manager...")

        # 모든 구독 해제
        await self.unsubscribe_all()

        # 코디네이터 중지
        if self.coordinator:
            await self.coordinator.stop()

        # 연결 풀 중지
        await websocket_pool.stop()

        # 레거시 Binance 클라이언트 정리
        if self.binance_client:
            await self.binance_client.close_connection()

        logger.info("✅ WebSocket manager closed successfully")


# Global singleton instance
websocket_manager = WebSocketManager()
