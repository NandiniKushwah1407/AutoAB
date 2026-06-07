from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy import create_engine
from config import get_settings

settings = get_settings()

# ── Async engine (used by FastAPI endpoints) ──────────────────
async_engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    pool_pre_ping=True,
)

AsyncSessionLocal = sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# ── Sync engine (used by Celery workers) ─────────────────────
sync_engine = create_engine(
    settings.sync_database_url,
    echo=False,
    pool_pre_ping=True,
)


class Base(DeclarativeBase):
    pass


# ── FastAPI dependency ────────────────────────────────────────
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


# ── Called on app startup to create all tables ────────────────
async def create_tables():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
