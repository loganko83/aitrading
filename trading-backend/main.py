from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "testnet": settings.BINANCE_TESTNET
    }


@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "database": "connected",  # TODO: Add actual DB check
        "binance": "connected",   # TODO: Add actual Binance check
        "redis": "connected"      # TODO: Add actual Redis check
    }


# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("Starting TradingBot AI Backend...")

    # TODO: Initialize market monitor for selected symbols
    # from app.workers.market_monitor import MarketMonitor
    # market_monitor = MarketMonitor(symbols=["BTCUSDT", "ETHUSDT"])
    # await market_monitor.start()

    logger.info("Backend started successfully")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down TradingBot AI Backend...")

    # TODO: Stop market monitor
    # await market_monitor.stop()

    # Close WebSocket connections
    from app.services.websocket_manager import websocket_manager
    await websocket_manager.close()

    logger.info("Backend shutdown complete")


# Import and include API routers
from app.api.v1 import trading, websocket as ws_router, strategies

app.include_router(
    trading.router,
    prefix=f"{settings.API_V1_PREFIX}/trading",
    tags=["Trading"]
)

app.include_router(
    strategies.router,
    prefix=f"{settings.API_V1_PREFIX}",
    tags=["Strategies"]
)

app.include_router(
    ws_router.router,
    prefix="/ws",
    tags=["WebSocket"]
)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,  # Use port 8001 to avoid conflict with existing Llama server
        reload=settings.DEBUG
    )
