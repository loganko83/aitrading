from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
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

# Prometheus metrics instrumentation
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST, REGISTRY
from fastapi import Response

# Custom metrics for trading system (with safe registration)
try:
    orders_total = Counter('orders_total', 'Total number of orders', ['exchange', 'action', 'status'])
    order_failures_total = Counter('order_failures_total', 'Total number of failed orders', ['exchange', 'reason'])
    trades_total = Counter('trades_total', 'Total number of completed trades', ['exchange', 'symbol'])
    trading_volume_usd = Counter('trading_volume_usd', 'Total trading volume in USD', ['exchange', 'symbol'])

    exchange_api_up = Gauge('exchange_api_up', 'Exchange API availability', ['exchange'])
    websocket_connected = Gauge('websocket_connected', 'WebSocket connection status', ['exchange'])
    active_positions = Gauge('active_positions', 'Number of active positions', ['exchange', 'symbol'])
    portfolio_value_usd = Gauge('portfolio_value_usd', 'Total portfolio value in USD', ['user_id'])
    portfolio_drawdown_percent = Gauge('portfolio_drawdown_percent', 'Portfolio drawdown percentage', ['user_id'])

    http_request_duration_seconds = Histogram('http_request_duration_seconds', 'HTTP request latency',
                                               ['method', 'endpoint', 'status'])
except ValueError:
    # Metrics already registered (hot reload scenario) - retrieve existing collectors
    for collector in list(REGISTRY._collector_to_names.keys()):
        if hasattr(collector, '_name'):
            if collector._name == 'orders_total':
                orders_total = collector
            elif collector._name == 'order_failures_total':
                order_failures_total = collector
            elif collector._name == 'trades_total':
                trades_total = collector
            elif collector._name == 'trading_volume_usd':
                trading_volume_usd = collector
            elif collector._name == 'exchange_api_up':
                exchange_api_up = collector
            elif collector._name == 'websocket_connected':
                websocket_connected = collector
            elif collector._name == 'active_positions':
                active_positions = collector
            elif collector._name == 'portfolio_value_usd':
                portfolio_value_usd = collector
            elif collector._name == 'portfolio_drawdown_percent':
                portfolio_drawdown_percent = collector
            elif collector._name == 'http_request_duration_seconds':
                http_request_duration_seconds = collector

# Metrics endpoint
@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

# Register exception handlers
from app.core.exceptions import register_exception_handlers
register_exception_handlers(app)

# CORS configuration (Docker-compatible)
# Read from environment variable (comma-separated)
cors_origins = [origin.strip() for origin in settings.CORS_ORIGINS.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# GZIP Compression for API responses
app.add_middleware(
    GZipMiddleware,
    minimum_size=500  # Compress responses larger than 500 bytes
)

logger.info(f"CORS enabled for origins: {cors_origins}")
logger.info("GZIP compression enabled for responses > 500 bytes")


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "testnet": settings.BINANCE_TESTNET,
        "version": "1.2.0",
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
                "cache_warmup": "enabled",
                "gzip_compression": "enabled"
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

    # Initialize database (with Slow Query Logger)
    logger.info("Initializing database connection...")
    from app.database.base import engine
    logger.info("✅ Database initialized with query performance monitoring")

    # Initialize cache system
    from app.core.cache import initialize_cache, cache_cleanup_task
    import asyncio

    logger.info("Initializing cache system...")
    initialize_cache()  # Warm up preset and strategy caches

    # Start background cache cleanup task
    logger.info("Starting background cache cleanup task...")
    asyncio.create_task(cache_cleanup_task())

    # Initialize Redis client
    logger.info("Initializing Redis client...")
    from app.core.redis_client import RedisClient
    try:
        await RedisClient.get_client()
        logger.info("✅ Redis client initialized successfully")
    except Exception as e:
        logger.warning(f"⚠️ Redis initialization failed: {e}. Caching will be disabled.")

    # Start risk monitoring service
    logger.info("Starting risk monitoring service...")
    from app.workers.risk_monitor import start_risk_monitor
    asyncio.create_task(start_risk_monitor())

    # Initialize WebSocket connection pool
    logger.info("Initializing WebSocket connection pool...")
    from app.services.websocket_pool import websocket_pool
    await websocket_pool.start()
    logger.info("✅ WebSocket connection pool started")

    # Initialize WebSocket coordinator (worker communication)
    logger.info("Initializing WebSocket coordinator...")
    from app.services.websocket_manager import websocket_manager
    from app.core.redis_pubsub import WebSocketCoordinator
    websocket_manager.coordinator = WebSocketCoordinator(websocket_manager.worker_id)
    await websocket_manager.coordinator.start()
    logger.info(f"✅ WebSocket coordinator started (worker: {websocket_manager.worker_id})")

    # TODO: Initialize market monitor for selected symbols
    # from app.workers.market_monitor import MarketMonitor
    # market_monitor = MarketMonitor(symbols=["BTCUSDT", "ETHUSDT"])
    # await market_monitor.start()

    logger.info(
        "✅ Backend started successfully with:\n"
        "  - Database query optimization (18 indexes + slow query monitoring)\n"
        "  - Redis caching system\n"
        "  - WebSocket connection pooling and scaling\n"
        "  - Risk monitoring\n"
        "  - Worker coordination (Redis Pub/Sub)"
    )


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down TradingBot AI Backend...")

    # Stop risk monitoring service
    from app.workers.risk_monitor import stop_risk_monitor
    await stop_risk_monitor()

    # Stop WebSocket coordinator and connection pool
    from app.services.websocket_manager import websocket_manager
    from app.services.websocket_pool import websocket_pool

    logger.info("Stopping WebSocket coordinator...")
    if websocket_manager.coordinator:
        await websocket_manager.coordinator.stop()

    logger.info("Stopping WebSocket connection pool...")
    await websocket_pool.stop()

    logger.info("Closing WebSocket connections...")
    await websocket_manager.close()

    # Close Redis connection
    from app.core.redis_client import RedisClient
    await RedisClient.close()
    logger.info("Redis client closed")

    # TODO: Stop market monitor
    # await market_monitor.stop()

    logger.info("✅ Backend shutdown complete")


# Import and include API routers
from app.api.v1 import trading, websocket as ws_router, strategies, backtest, simple, health, performance, optimize, webhook, accounts, accounts_secure, telegram, pine_script, symbols, market, positions, portfolio, ai_prediction, signal, auth

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

# Authentication API (Login, Register, 2FA)
app.include_router(
    auth.router,
    prefix=f"{settings.API_V1_PREFIX}",
    tags=["🔑 Authentication"]
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

# AI Price Prediction API (LSTM Deep Learning)
app.include_router(
    ai_prediction.router,
    prefix=f"{settings.API_V1_PREFIX}",
    tags=["🧠 AI Price Prediction (LSTM)"]
)

# Real-time Signal Generation API (LSTM + Technical + LLM)
app.include_router(
    signal.router,
    prefix=f"{settings.API_V1_PREFIX}",
    tags=["🎯 Real-time Trading Signals (AI Ensemble)"]
)

# Symbol Management API (Multi-Coin Support)
app.include_router(
    symbols.router,
    prefix=f"{settings.API_V1_PREFIX}",
    tags=["📊 Symbol Management"]
)

# Market Data API (Real-time Prices & 24h Stats)
app.include_router(
    market.router,
    prefix=f"{settings.API_V1_PREFIX}",
    tags=["📈 Market Data"]
)

# Position Management API (Multi-Symbol & Portfolio)
app.include_router(
    positions.router,
    prefix=f"{settings.API_V1_PREFIX}",
    tags=["💼 Position Management"]
)

# Portfolio Analysis API (Advanced Features)
app.include_router(
    portfolio.router,
    prefix=f"{settings.API_V1_PREFIX}/portfolio",
    tags=["📊 Portfolio Analysis (Advanced)"]
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
