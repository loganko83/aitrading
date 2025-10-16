import asyncio
import json
from typing import Dict, Set, Callable
from fastapi import WebSocket
from binance import AsyncClient, BinanceSocketManager
import logging

logger = logging.getLogger(__name__)


class WebSocketManager:
    """
    WebSocket manager for real-time market data streaming

    Manages connections to Binance WebSocket for market data
    and broadcasts to connected frontend clients
    """

    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.binance_client: AsyncClient = None
        self.binance_socket_manager: BinanceSocketManager = None
        self.active_streams: Dict[str, asyncio.Task] = {}
        self.subscribed_symbols: Set[str] = set()

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

    async def subscribe_ticker(self, symbol: str):
        """
        Subscribe to ticker updates for a symbol

        Streams: price, 24h volume, 24h high/low, price change %
        """
        if symbol in self.subscribed_symbols:
            logger.info(f"Already subscribed to {symbol}")
            return

        try:
            # Create ticker stream
            ticker_socket = self.binance_socket_manager.symbol_ticker_socket(symbol)

            # Start streaming task
            task = asyncio.create_task(
                self._stream_ticker(ticker_socket, symbol)
            )

            self.active_streams[f"ticker_{symbol}"] = task
            self.subscribed_symbols.add(symbol)

            logger.info(f"Subscribed to ticker stream for {symbol}")

        except Exception as e:
            logger.error(f"Error subscribing to ticker {symbol}: {e}")
            raise

    async def _stream_ticker(self, ticker_socket, symbol: str):
        """Internal method to stream ticker data"""
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

    async def unsubscribe_all(self):
        """Unsubscribe from all active streams"""
        for stream_key in list(self.active_streams.keys()):
            await self.unsubscribe(stream_key)

        logger.info("Unsubscribed from all streams")

    async def close(self):
        """Close all connections and cleanup"""
        await self.unsubscribe_all()

        if self.binance_client:
            await self.binance_client.close_connection()

        logger.info("WebSocket manager closed")


# Global singleton instance
websocket_manager = WebSocketManager()
