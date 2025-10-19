"""Database base configuration"""

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

# Convert PostgreSQL URL to async format
database_url = settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

# Create async engine
engine = create_async_engine(
    database_url,
    echo=settings.DEBUG,
    future=True
)

# Create async session factory
AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Base class for all models
Base = declarative_base()

# =======================
# Query Performance Monitoring
# =======================

# Initialize Slow Query Logger (1초 이상 소요되는 쿼리 자동 감지)
from app.database.query_optimization import slow_query_logger

try:
    slow_query_logger.setup_event_listeners(engine.sync_engine)
    logger.info("✅ Slow Query Logger initialized (threshold: 1.0s)")
except Exception as e:
    logger.warning(f"⚠️ Failed to initialize Slow Query Logger: {e}")


# Dependency for database sessions
async def get_db():
    """
    데이터베이스 세션 의존성

    FastAPI 엔드포인트에서 Depends(get_db)로 사용
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
