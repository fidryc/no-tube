from app.core.config import settings
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

engine = create_async_engine(settings.DB_URL)

session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
