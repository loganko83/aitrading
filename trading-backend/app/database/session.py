"""Database session management"""

from typing import Generator
from app.database.base import AsyncSessionLocal


async def get_db() -> Generator:
    """
    Dependency for getting async database session

    Usage:
        @router.get("/")
        async def route(db: AsyncSession = Depends(get_db)):
            ...
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
