from typing import Optional, Self
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.implementations.sqlalchemy.repositories import (
    UserRepository,
    VideoRepository,
    VideoStatsRepository,
    VideoUrlsRepository,
    LikesRepository,
    HistoryRepository,
    BlacklistRefreshRepository
)
from app.repositories.interfaces.uow import IUOW
from app.db.session import session_maker
from app.core.logger import logger


class UOW(IUOW):
    def __init__(self):
        self.session_factory = session_maker
        self.__session: Optional[AsyncSession] = None

        # репозитории
        self.__user_repo: Optional[UserRepository] = None
        self.__video_repo: Optional[VideoRepository] = None
        self.__video_stats_repo: Optional[VideoStatsRepository] = None
        self.__video_urls_repo: Optional[VideoUrlsRepository] = None
        self.__likes_repo: Optional[LikesRepository] = None
        self.__history_repo: Optional[HistoryRepository] = None
        self.__blacklist_refresh_repo: Optional[BlacklistRefreshRepository] = None

    async def __aenter__(self) -> Self:
        self.__session = self.session_factory()
        logger.debug("UOW enter")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        if self.__session is None:
            return
        try:
            if exc_type is not None:
                await self.rollback()
            else:
                await self.commit()
        finally:
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
        logger.debug("UOW commit")

    async def close(self) -> None:
        if self.__session is None:
            return
        await self.__session.close()
        self.__session = None
        logger.debug("UOW close")

    @property
    def user_repo(self) -> UserRepository:
        if self.__user_repo is None and self.__session is not None:
            self.__user_repo = UserRepository(self.__session)
        return self.__user_repo

    @property
    def video_repo(self) -> VideoRepository:
        if self.__video_repo is None and self.__session is not None:
            self.__video_repo = VideoRepository(self.__session)
        return self.__video_repo

    @property
    def video_stats_repo(self) -> VideoStatsRepository:
        if self.__video_stats_repo is None and self.__session is not None:
            self.__video_stats_repo = VideoStatsRepository(self.__session)
        return self.__video_stats_repo

    @property
    def video_urls_repo(self) -> VideoUrlsRepository:
        if self.__video_urls_repo is None and self.__session is not None:
            self.__video_urls_repo = VideoUrlsRepository(self.__session)
        return self.__video_urls_repo

    @property
    def likes_repo(self) -> LikesRepository:
        if self.__likes_repo is None and self.__session is not None:
            self.__likes_repo = LikesRepository(self.__session)
        return self.__likes_repo

    @property
    def history_repo(self) -> HistoryRepository:
        if self.__history_repo is None and self.__session is not None:
            self.__history_repo = HistoryRepository(self.__session)
        return self.__history_repo

    @property
    def blacklist_refresh_repo(self) -> BlacklistRefreshRepository:
        if self.__blacklist_refresh_repo is None and self.__session is not None:
            self.__blacklist_refresh_repo = BlacklistRefreshRepository(self.__session)
        return self.__blacklist_refresh_repo