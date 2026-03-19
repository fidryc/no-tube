from dataclasses import dataclass
import datetime
from typing import Optional

from app.domain.enums import ProcessingStatuses, Roles, Visibility


@dataclass(frozen=True)
class UserEntity:
    id: int
    username: str
    email: str
    role: Roles
    created_at: datetime.datetime
    is_confirmed: bool
    hashed_password: Optional[str] = None


@dataclass(frozen=True)
class VideoEntity:
    id: int
    title: str
    description: str
    user_id: int
    processing_status: ProcessingStatuses
    visibility: Visibility
    created_at: datetime.datetime
    

@dataclass(frozen=True)
class VideoStatsEntity:
    video_id: int
    likes: int
    views: int
    

@dataclass(frozen=True)
class VideoUrlEntity:
    id: int
    video_id: int
    url: str
    quality: str
    format: str
    bitrate: int
    codec: str
    size_bytes: int
    is_default: bool
    

@dataclass(frozen=True)
class LikeEntity:
    video_id: int
    user_id: int
    created_at: datetime.datetime
    

@dataclass(frozen=True)
class HistoryEntity:
    video_id: int
    user_id: int
    watched_at: datetime.datetime
    
    
@dataclass(frozen=True)
class SessionEntity:
    id: str
    user_id: int
    expires_at: datetime.datetime