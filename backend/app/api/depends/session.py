from typing import Annotated

from fastapi import Depends
from app.db.session import session_maker
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.implementations.sqlalchemy.uow import UOW

async def get_session():
    async with session_maker() as session:
        yield session
        
SessionDep = Annotated[AsyncSession, Depends(get_session)]