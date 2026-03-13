from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

_engine = None
_AsyncSessionLocal = None


def _get_session_factory():
    global _engine, _AsyncSessionLocal
    if _engine is None:
        from app.core.config import settings
        _engine = create_async_engine(
            settings.DATABASE_URL,
            echo=settings.DEBUG,
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20,
        )
        _AsyncSessionLocal = async_sessionmaker(
            _engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
    return _AsyncSessionLocal


async def get_db() -> AsyncSession:
    session_factory = _get_session_factory()
    async with session_factory() as session:
        try:
            yield session
        finally:
            await session.close()
