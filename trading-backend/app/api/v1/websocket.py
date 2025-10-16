from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.services.websocket_manager import websocket_manager
from app.core.config import settings
import logging
import json

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/market")
async def websocket_market_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time market data

    Client can send commands:
    - {"action": "subscribe_ticker", "symbol": "BTCUSDT"}
    - {"action": "subscribe_kline", "symbol": "BTCUSDT", "interval": "1m"}
    - {"action": "subscribe_trades", "symbol": "BTCUSDT"}
    - {"action": "unsubscribe", "stream": "ticker_BTCUSDT"}
    """
    await websocket_manager.connect(websocket)

    # Initialize Binance client if not already done
    if not websocket_manager.binance_client:
        try:
            await websocket_manager.initialize_binance_client(
                api_key=settings.BINANCE_API_KEY,
                api_secret=settings.BINANCE_API_SECRET
            )
        except Exception as e:
            logger.error(f"Failed to initialize Binance client: {e}")
            await websocket.close(code=1011, reason="Failed to connect to Binance")
            return

    try:
        while True:
            # Receive commands from client
            data = await websocket.receive_text()
            message = json.loads(data)

            action = message.get("action")
            symbol = message.get("symbol")

            if action == "subscribe_ticker" and symbol:
                await websocket_manager.subscribe_ticker(symbol)
                await websocket.send_json({
                    "status": "subscribed",
                    "type": "ticker",
                    "symbol": symbol
                })

            elif action == "subscribe_kline" and symbol:
                interval = message.get("interval", "1m")
                await websocket_manager.subscribe_kline(symbol, interval)
                await websocket.send_json({
                    "status": "subscribed",
                    "type": "kline",
                    "symbol": symbol,
                    "interval": interval
                })

            elif action == "subscribe_trades" and symbol:
                await websocket_manager.subscribe_trades(symbol)
                await websocket.send_json({
                    "status": "subscribed",
                    "type": "trades",
                    "symbol": symbol
                })

            elif action == "unsubscribe":
                stream_key = message.get("stream")
                if stream_key:
                    await websocket_manager.unsubscribe(stream_key)
                    await websocket.send_json({
                        "status": "unsubscribed",
                        "stream": stream_key
                    })

            elif action == "ping":
                await websocket.send_json({"type": "pong"})

            else:
                await websocket.send_json({
                    "error": "Invalid action or missing parameters"
                })

    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket)
        logger.info("WebSocket client disconnected")

    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        websocket_manager.disconnect(websocket)


@router.websocket("/positions")
async def websocket_positions_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time position updates

    Streams:
    - Position P&L changes
    - Liquidation price updates
    - Margin updates
    """
    await websocket.accept()

    try:
        # TODO: Implement position monitoring
        # For now, send a placeholder message
        await websocket.send_json({
            "type": "positions",
            "message": "Position monitoring will be implemented"
        })

        while True:
            data = await websocket.receive_text()
            # Handle position-related commands

    except WebSocketDisconnect:
        logger.info("Position WebSocket client disconnected")

    except Exception as e:
        logger.error(f"Position WebSocket error: {e}")
