from typing import Optional, Protocol, Self

from app.repositories.interfaces.repositories import IAuthorSubscriptionRepository, IBalanceRepository, IHistoryRepository, ILikesRepository, IOauthAccountRepository, IPaymentRepository, ISessionRepository, IUserRepository, IUserSubscriptionRepository, IVideoRepository, IVideoStatsRepository, IVideoUrlsRepository

class IUOW(Protocol):
    def __init__(self):
        self.__user_repo: Optional[IUserRepository] = None
        self.__video_repo: Optional[IVideoRepository] = None
        self.__video_stats_repo: Optional[IVideoStatsRepository] = None
        self.__video_urls_repo: Optional[IVideoUrlsRepository] = None
        self.__likes_repo: Optional[ILikesRepository] = None
        self.__history_repo: Optional[IHistoryRepository] = None
        self.__session_repo: Optional[ISessionRepository] = None
        self.__oauth_account_repo: Optional[IOauthAccountRepository] = None
        self.__author_subscriptions_repo: Optional[IAuthorSubscriptionRepository] = None
        self.__user_subscriptions_repo: Optional[IUserSubscriptionRepository] = None
        self.__payment_repo: Optional[IPaymentRepository] = None
        self.__balance_repo: Optional[IBalanceRepository] = None

    async def __aenter__(self) -> Self: ...
    async def __aexit__(self, exc_type, exc, tb) -> None: ...
    async def rollback(self) -> None: ...
    async def commit(self) -> None: ...
    async def close(self) -> None: ...

    @property
    def user_repo(self) -> IUserRepository:
        return self.__user_repo 

    @property
    def video_repo(self) -> IVideoRepository:
        return self.__video_repo

    @property
    def video_stats_repo(self) -> IVideoStatsRepository:
        return self.__video_stats_repo

    @property
    def video_urls_repo(self) -> IVideoUrlsRepository:
        return self.__video_urls_repo

    @property
    def likes_repo(self) -> ILikesRepository:
        return self.__likes_repo

    @property
    def history_repo(self) -> IHistoryRepository:
        return self.__history_repo

    @property
    def session_repo(self) -> ISessionRepository:
        return self.__session_repo
    
    @property
    def oauth_account_repo(self) -> IOauthAccountRepository:
        return self.__oauth_account_repo
    
    @property
    def author_subscriptions_repo(self) -> IAuthorSubscriptionRepository:
        return self.__author_subscriptions_repo
    
    @property
    def user_subscriptions_repo(self) -> IUserSubscriptionRepository:
        return self.__user_subscriptions_repo
    
    @property
    def payment_repo(self) -> IPaymentRepository:
        return self.__payment_repo
    
    @property
    def balance_repo(self) -> IBalanceRepository:
        return self.__balance_repo