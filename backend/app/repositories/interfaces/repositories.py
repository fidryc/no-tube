from app.repositories.interfaces.base_repository import IRepository
from typing import Protocol, TypeVar
from app.domain.entitites import (
    UserEntity,
    VideoEntity,
    VideoStatsEntity,
    VideoUrlEntity,
    LikeEntity,
    HistoryEntity,
    SessionEntity,
    OauthAccountEntity
)

Model = TypeVar("Model")


class IUserRepository(IRepository[Model, UserEntity], Protocol):
    pass


class IVideoRepository(IRepository[Model, VideoEntity], Protocol):
    pass


class IVideoStatsRepository(IRepository[Model, VideoStatsEntity], Protocol):
    pass


class IVideoUrlsRepository(IRepository[Model, VideoUrlEntity], Protocol):
    pass


class ILikesRepository(IRepository[Model, LikeEntity], Protocol):
    pass


class IHistoryRepository(IRepository[Model, HistoryEntity], Protocol):
    pass


class ISessionRepository(IRepository[Model, SessionEntity], Protocol):
    pass

class IOauthAccountRepository(IRepository[Model, OauthAccountEntity], Protocol):
    pass