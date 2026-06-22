from app.repositories.interfaces.base_repository import IRepository
from typing import Protocol, TypeVar
from app.domain.entitites import (
    AuthorSubscriptionEntity,
    BalanceEntity,
    PaymentEntity,
    UserEntity,
    UserSubscriptionEntity,
    VideoEntity,
    VideoStatsEntity,
    VideoUrlEntity,
    LikeEntity,
    HistoryEntity,
    SessionEntity,
    OauthAccountEntity,
    VideoWithUserSchema
)
from app.db.models import Balance
from app.repositories.filter.filter import And, Filter, Not, Or

Model = TypeVar("Model")


class IUserRepository(IRepository[Model, UserEntity], Protocol):
    pass


class IVideoRepository(IRepository[Model, VideoEntity], Protocol):
    async def get_by_filters_with_users(
        self,
        *filters: And | Or | Not | Filter,
        order_by_col_title: str | None = None,
        desc: bool | None = None,
        limit: int | None = None,
        offset: int | None = None
    ) -> list[VideoWithUserSchema]: pass


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


class IAuthorSubscriptionRepository(IRepository[Model, AuthorSubscriptionEntity], Protocol):
    pass


class IUserSubscriptionRepository(IRepository[Model, UserSubscriptionEntity], Protocol):
    pass


class IPaymentRepository(IRepository[Model, PaymentEntity], Protocol):
    pass

class IBalanceRepository(IRepository[Model, BalanceEntity], Protocol):
    pass