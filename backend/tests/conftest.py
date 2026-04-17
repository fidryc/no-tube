import asyncio
import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

from app.core.config import settings
from app.db.models import Base


@pytest.fixture(scope="session")
async def engine_fixture():
    engine = create_async_engine(
        settings.DB_URL,
        # poolclass=NullPool,  # каждый раз новое соединение, без пула
    )
    yield engine
    await engine.dispose()


@pytest.fixture(scope="session")
async def prepare_db(engine_fixture):
    assert settings.MODE == "TEST"

    async with engine_fixture.begin() as conn:
        await conn.execute(text("DROP SCHEMA public CASCADE"))
        await conn.execute(text("CREATE SCHEMA public"))
        await conn.run_sync(Base.metadata.create_all)


@pytest.fixture(scope="function")
async def session(engine_fixture, prepare_db):
    session_maker = async_sessionmaker(engine_fixture, expire_on_commit=False)

    async with session_maker() as s:
        try:
            yield s
            await s.rollback()
        except Exception:
            await s.rollback()
            raise
        finally:
            await s.close()