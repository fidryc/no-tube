from contextlib import asynccontextmanager
from re import S
from typing import Optional, Self
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.implementations.sqlalchemy.repositories import (
    AuthorSubscriptionRepository,
    BalanceRepository,
    OauthAccountRepository,
    PaymentRepository,
    SessionRepository,
    UserRepository,
    UserSubscriptionRepository,
    VideoRepository,
    VideoStatsRepository,
    VideoUrlsRepository,
    LikesRepository,
    HistoryRepository
)
from app.repositories.interfaces.uow import IUOW
from app.db.session import async_session_maker
from app.core.logger import logger
from app.repositories.exceptions import UOWException


class UOW(IUOW):
    def __init__(self, isolation_level: Optional[str] = None):
        self.session_factory = async_session_maker
        self.__session: Optional[AsyncSession] = None
        self._isolation_level = isolation_level

        self.__user_repo: Optional[UserRepository] = None
        self.__video_repo: Optional[VideoRepository] = None
        self.__video_stats_repo: Optional[VideoStatsRepository] = None
        self.__video_urls_repo: Optional[VideoUrlsRepository] = None
        self.__likes_repo: Optional[LikesRepository] = None
        self.__history_repo: Optional[HistoryRepository] = None
        self.__session_repo: Optional[SessionRepository] = None
        self.__oauth_account_repo: Optional[OauthAccountRepository] = None
        self.__author_subscriptions_repo: Optional[AuthorSubscriptionRepository] = None
        self.__user_subscriptions_repo: Optional[UserSubscriptionRepository] = None
        self.__payment_repo: Optional[PaymentRepository] = None
        self.__balance_repo: Optional[BalanceRepository] = None
        
    async def __aenter__(self) -> Self:
        self.__session = self.session_factory()
        if self._isolation_level:
            (await self.__session.connection()).execution_options(
                isolation_level=self._isolation_level
            )
            logger.debug(f"UOW change isolation level on {self._isolation_level}")
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
    def session_repo(self) -> SessionRepository:
        if self.__session_repo is None and self.__session is not None:
            self.__session_repo = SessionRepository(self.__session)
        return self.__session_repo
    
    @property
    def oauth_account_repo(self) -> OauthAccountRepository:
        if self.__oauth_account_repo is None and self.__session is not None:
            self.__oauth_account_repo = OauthAccountRepository(self.__session)
        return self.__oauth_account_repo
    
    @property
    def author_subscriptions_repo(self) -> AuthorSubscriptionRepository:
        if self.__author_subscriptions_repo is None and self.__session is not None:
            self.__author_subscriptions_repo = AuthorSubscriptionRepository(self.__session)
        return self.__author_subscriptions_repo
    
    @property
    def user_subscriptions_repo(self) -> UserSubscriptionRepository:
        if self.__user_subscriptions_repo is None and self.__session is not None:
            self.__user_subscriptions_repo = UserSubscriptionRepository(self.__session)
        return self.__user_subscriptions_repo
    
    @property
    def payment_repo(self) -> PaymentRepository:
        if self.__payment_repo is None and self.__session is not None:
            self.__payment_repo = PaymentRepository(self.__session)
        return self.__payment_repo
    
    @property
    def balance_repo(self) -> BalanceRepository:
        if self.__balance_repo is None and self.__session is not None:
            self.__balance_repo = BalanceRepository(self.__session)
        return self.__balance_repo