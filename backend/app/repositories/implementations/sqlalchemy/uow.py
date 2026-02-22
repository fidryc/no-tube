from typing import Optional, Self
from app.repositories.implementations.sqlalchemy.repositories import UserRepository
from app.repositories.interfaces.uow import IUOW
from app.db.session import session_maker
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.logger import logger


class UOW(IUOW):
    def __init__(self):
        self.sessio_factory = session_maker
        self.__session: Optional[AsyncSession] = None
        
        self.__user_repo = None
    
    async def __aenter__(self) -> Self:
        async with session_maker() as session:
            self.__session = session
            logger.debug("UOW enter")
            return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        if self.__session is None:
            return
        if exc_type is not None:
            await self.rollback()
        else:
            await self.commit()
        await self.close()
        logger.debug("UOW exit")
    
    async def rollback(self) -> None:
        if self.__session is None:
            return
        await self.__session.rollback()
        logger.debug("UOW rollback")
        
    
    async def commit(self) -> None:
        if self.__session is None:
            return
        await self.__session.commit()
    
    async def close(self) -> None:
        if self.__session is None:
            return
        await self.__session.close()
        
    @property
    def user_repo(self) -> UserRepository:
        if self.__user_repo is not None:
            return self.__user_repo
        if self.__session is not None:
            return UserRepository(self.__session)