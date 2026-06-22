# from dataclasses import dataclass
# Подменяю пока, чтобы не делать для каждой модели еще и схему для апи
import uuid

from pydantic import BaseModel
from pydantic.dataclasses import dataclass
import datetime
import decimal
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
    avatar_key: Optional[str] = None
    
    
class UserSchema(BaseModel):
    id: int
    username: str
    email: str
    role: Roles
    created_at: datetime.datetime
    is_confirmed: bool
    avatar_key: Optional[str] = None


@dataclass(frozen=True)
class VideoEntity:
    id: uuid.UUID
    title: str
    description: str
    user_id: int
    processing_status: ProcessingStatuses
    visibility: Visibility
    created_at: datetime.datetime
    preview_key: Optional[str] = None
    
class VideoWithUserSchema(BaseModel):
    id: uuid.UUID
    title: str
    description: str
    user_id: int
    processing_status: ProcessingStatuses
    visibility: Visibility
    created_at: datetime.datetime
    user: UserSchema
    preview_key: Optional[str] = None
    
    
@dataclass(frozen=True)
class VideoStatsEntity:
    video_id: uuid.UUID
    likes: int
    views: int
    

@dataclass(frozen=True)
class VideoUrlEntity:
    id: int
    video_id: uuid.UUID
    url: str
    quality: str
    format: str
    bitrate: int
    codec: str
    size_bytes: int
    is_default: bool
    

@dataclass(frozen=True)
class LikeEntity:
    video_id: uuid.UUID
    user_id: int
    created_at: datetime.datetime
    

@dataclass(frozen=True)
class HistoryEntity:
    video_id: uuid.UUID
    user_id: int
    watched_at: datetime.datetime
    
    
@dataclass(frozen=True)
class SessionEntity:
    id: str
    user_id: int
    expires_at: datetime.datetime
    
@dataclass(frozen=True)
class OauthAccountEntity:
    provider: str
    provider_user_id: str
    user_id: int
    created_at: datetime.datetime
   
@dataclass(frozen=True)
class AuthorSubscriptionEntity:
    id: int
    author_id: int
    days: int
    price: decimal.Decimal
    
@dataclass(frozen=True)
class UserSubscriptionEntity:
    id: int
    user_id: int
    author_subscription_id: int
    expires_at: datetime.datetime
    
    
@dataclass(frozen=True)
class PaymentEntity:
    id: uuid.UUID
    user_id: int
    author_subscription_id: int
    status: int
    amount: decimal.Decimal
    created_at: datetime.datetime
    provider_payment_id: Optional[str] = None
    
    
@dataclass(frozen=True)
class BalanceEntity:
    id: uuid.UUID
    user_id: int
    amount: decimal.Decimal
    
    