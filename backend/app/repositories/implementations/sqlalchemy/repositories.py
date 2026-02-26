from app.db.models import (
    User,
    Video,
    VideoStats,
    VideoUrls,
    Likes,
    History,
    BlacklistRefresh
)
from app.repositories.interfaces.base_repository import IRepository
from app.repositories.implementations.sqlalchemy.base_repository import Repository
from app.domain.entitites import (
    UserEntity,
    VideoEntity,
    VideoStatsEntity,
    VideoUrlEntity,
    LikeEntity,
    HistoryEntity,
    BlacklistRefreshEntity
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


class BlacklistRefreshRepository(Repository[BlacklistRefresh, BlacklistRefreshEntity]):
    model = BlacklistRefresh
    entity = BlacklistRefreshEntity