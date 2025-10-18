from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
import logging

# Initialize logging system
from app.core.logging_config import setup_logging
setup_logging(log_level="DEBUG" if settings.DEBUG else "INFO")

logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Register exception handlers
from app.core.exceptions import register_exception_handlers
register_exception_handlers(app)

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
        "testnet": settings.BINANCE_TESTNET,
        "version": "1.1.0",
        "features": {
            "stability": {
                "retry_logic": "enabled",
                "circuit_breaker": "enabled",
                "timeout_protection": "enabled",
                "graceful_degradation": "enabled"
            },
            "performance": {
                "caching": "enabled",
                "performance_tracking": "enabled",
                "cache_warmup": "enabled"
            },
            "optimization": {
                "preset_system": "enabled",
                "exchange_optimization": "enabled",
                "auto_recommendation": "enabled"
            }
        }
    }


# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("Starting TradingBot AI Backend...")

    # Initialize cache system
    from app.core.cache import initialize_cache, cache_cleanup_task
    import asyncio

    logger.info("Initializing cache system...")
    initialize_cache()  # Warm up preset and strategy caches

    # Start background cache cleanup task
    logger.info("Starting background cache cleanup task...")
    asyncio.create_task(cache_cleanup_task())

    # TODO: Initialize market monitor for selected symbols
    # from app.workers.market_monitor import MarketMonitor
    # market_monitor = MarketMonitor(symbols=["BTCUSDT", "ETHUSDT"])
    # await market_monitor.start()

    logger.info("Backend started successfully with caching enabled")


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
from app.api.v1 import trading, websocket as ws_router, strategies, backtest, simple, health, performance, optimize, webhook, accounts, accounts_secure, telegram, pine_script

# Health monitoring (system stability status)
app.include_router(
    health.router,
    prefix=f"{settings.API_V1_PREFIX}",
    tags=["🔍 System Health & Monitoring"]
)

# Performance monitoring (cache & optimization)
app.include_router(
    performance.router,
    prefix=f"{settings.API_V1_PREFIX}/performance",
    tags=["⚡ Performance & Cache Management"]
)

# Simple API (user-friendly, recommended for beginners)
app.include_router(
    simple.router,
    prefix=f"{settings.API_V1_PREFIX}",
    tags=["✨ Simple API (Recommended)"]
)

# Optimization API (parameter tuning)
app.include_router(
    optimize.router,
    prefix=f"{settings.API_V1_PREFIX}/optimize",
    tags=["🧬 Parameter Optimization"]
)

# TradingView Webhook API (auto-trading)
app.include_router(
    webhook.router,
    prefix=f"{settings.API_V1_PREFIX}",
    tags=["📡 TradingView Webhooks"]
)

# Account Management API (API key registration)
app.include_router(
    accounts.router,
    prefix=f"{settings.API_V1_PREFIX}",
    tags=["👤 Account Management"]
)

# Secure Account Management API (with authentication & encryption)
app.include_router(
    accounts_secure.router,
    prefix=f"{settings.API_V1_PREFIX}",
    tags=["🔐 Secure Account Management (Recommended)"]
)

# Telegram Notification API
app.include_router(
    telegram.router,
    prefix=f"{settings.API_V1_PREFIX}",
    tags=["📱 Telegram Notifications"]
)

# Pine Script Strategy Management API
app.include_router(
    pine_script.router,
    prefix=f"{settings.API_V1_PREFIX}",
    tags=["🤖 AI Pine Script Generator"]
)

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
    backtest.router,
    prefix=f"{settings.API_V1_PREFIX}",
    tags=["Backtesting (Advanced)"]
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
