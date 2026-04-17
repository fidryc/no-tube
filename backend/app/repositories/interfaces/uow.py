from typing import Optional, Protocol, Self

from app.repositories.interfaces.repositories import IHistoryRepository, ILikesRepository, IOauthAccountRepository, ISessionRepository, IUserRepository, IVideoRepository, IVideoStatsRepository, IVideoUrlsRepository

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