"""SQLAlchemy async session factory."""
import re
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.core.config import settings


def _async_url(url: str) -> str:
    """Convert postgresql:// → postgresql+asyncpg:// for asyncpg driver."""
    return re.sub(r"^postgresql(\+\w+)?://", "postgresql+asyncpg://", url)


engine = create_async_engine(
    _async_url(settings.DATABASE_URL),
    echo=settings.DEBUG,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
)

AsyncSessionLocal = async_sessionmaker(
    engine, expire_on_commit=False, class_=AsyncSession
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session
