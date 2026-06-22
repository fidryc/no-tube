from sqlalchemy import select

from app.db.models import (
    AuthorSubscription,
    Balance,
    OauthAccount,
    Payment,
    Session,
    User,
    UserSubscription,
    Video,
    VideoStats,
    VideoUrls,
    Likes,
    History
)
from app.repositories.interfaces.base_repository import IRepository
from app.repositories.implementations.sqlalchemy.base_repository import DEFAULT_ERROR_DESCRIPTION, DEFAULT_ERROR_LACK_MODEL, Repository
from app.domain.entitites import (
    AuthorSubscriptionEntity,
    BalanceEntity,
    OauthAccountEntity,
    PaymentEntity,
    SessionEntity,
    UserEntity,
    UserSubscriptionEntity,
    VideoEntity,
    VideoStatsEntity,
    VideoUrlEntity,
    LikeEntity,
    HistoryEntity,
    VideoWithUserSchema
)
from app.repositories.filter.filter import And, Filter, Not, Or
from app.repositories.exceptions import BaseRepositoryException
from sqlalchemy.exc import SQLAlchemyError
from app.core.logger import logger
from sqlalchemy.orm import joinedload

class UserRepository(Repository[User, UserEntity]):
    model = User
    entity = UserEntity


class VideoRepository(Repository[Video, VideoEntity]):
    model = Video
    entity = VideoEntity
    
    async def get_by_filters_with_users(
        self,
        *filters: And | Or | Not | Filter,
        order_by_col_title: str | None = None,
        desc: bool | None = None,
        limit: int | None = None,
        offset: int | None = None
    ) -> list[VideoWithUserSchema]:
        if not self.model:
            raise BaseRepositoryException(DEFAULT_ERROR_LACK_MODEL)
        query = select(self.model).where(*[self.to_expression(fil) for fil in filters]).options(joinedload(self.model.user))
        if order_by_col_title is not None:
            col = getattr(self.model, order_by_col_title)
            if desc is True:
                col = col.desc()
            query = query.order_by(col)
        if limit is not None:
            query = query.limit(limit)
        if offset is not None:
            query = query.offset(offset)
        try:
            models = (await self.session.execute(query)).scalars().all()
            return [VideoWithUserSchema.model_validate(model, from_attributes=True) for model in models]
        except SQLAlchemyError as e:
            logger.critical(
                msg=f"{self.__class__.__name__}: Error getting data from method 'get_by_filters'",
                exc_info=True,
                extra=filters
            )
            raise BaseRepositoryException(DEFAULT_ERROR_DESCRIPTION) from e
    


class VideoStatsRepository(Repository[VideoStats, VideoStatsEntity]):
    model = VideoStats
    entity = VideoStatsEntity


class VideoUrlsRepository(Repository[VideoUrls, VideoUrlEntity]):
    model = VideoUrls
    entity = VideoUrlEntity


class LikesRepository(Repository[Likes, LikeEntity]):
    model = Likes
    entity = LikeEntity


class HistoryRepository(Repository[History, HistoryEntity]):
    model = History
    entity = HistoryEntity


class SessionRepository(Repository[Session, SessionEntity]):
    model = Session
    entity = SessionEntity
    

class OauthAccountRepository(Repository[OauthAccount, OauthAccountEntity]):
    model = OauthAccount
    entity = OauthAccountEntity
    
    
class AuthorSubscriptionRepository(Repository[AuthorSubscription, AuthorSubscriptionEntity]):
    model = AuthorSubscription
    entity = AuthorSubscriptionEntity
    
    
class UserSubscriptionRepository(Repository[UserSubscription, UserSubscriptionEntity]):
    model = UserSubscription
    entity = UserSubscriptionEntity
    

class PaymentRepository(Repository[Payment, PaymentEntity]):
    model = Payment
    entity = PaymentEntity
    
class BalanceRepository(Repository[Balance, BalanceEntity]):
    model = Balance
    entity = BalanceEntity