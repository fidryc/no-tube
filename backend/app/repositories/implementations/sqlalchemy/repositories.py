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
from app.repositories.implementations.sqlalchemy.base_repository import Repository
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
    HistoryEntity
)


class UserRepository(Repository[User, UserEntity]):
    model = User
    entity = UserEntity


class VideoRepository(Repository[Video, VideoEntity]):
    model = Video
    entity = VideoEntity


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