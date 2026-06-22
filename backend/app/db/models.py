import datetime
from decimal import Decimal
import uuid
from sqlalchemy.orm import DeclarativeBase, mapped_column, Mapped, relationship
from sqlalchemy import Integer, Numeric, PrimaryKeyConstraint, String, Boolean, ForeignKey, Enum, DateTime, UniqueConstraint, Uuid, func
from typing import Optional

from app.domain.enums import PaymentStatuses, ProcessingStatuses, Roles, Visibility


class Base(DeclarativeBase):
    pass

    
class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    avatar_key: Mapped[Optional[str]] = mapped_column(String(256), unique=True, nullable=True)
    username: Mapped[str] = mapped_column(String(64), nullable=False)
    email: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    hashed_password: Mapped[str] = mapped_column(String(256), nullable=True) # null because user can login with oauth2
    role: Mapped[Roles] = mapped_column(Enum(Roles, native_enum=False), index=True, nullable=False, default=Roles.USER)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=func.now())
    is_confirmed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, server_default="false")


class Video(Base):
    __tablename__ = "videos"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    preview_key: Mapped[Optional[str]] = mapped_column(String(256), unique=True, nullable=True)
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    description: Mapped[str] = mapped_column(String(512), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    processing_status: Mapped[ProcessingStatuses] = mapped_column(Enum(ProcessingStatuses, native_enum=False), nullable=False)
    visibility: Mapped[Visibility] = mapped_column(Enum(Visibility, native_enum=False), nullable=False, index=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=func.now())
    
    user: Mapped[User] = relationship("User")
    
class VideoStats(Base):
    __tablename__ = "video_stats"

    video_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(
            "videos.id",
            ondelete="CASCADE",
            onupdate="CASCADE"
        ),
        primary_key=True
    )
    likes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    views: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class VideoUrls(Base):
    __tablename__ = "video_urls"

    id: Mapped[int] = mapped_column(primary_key=True)
    video_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(
            "videos.id",
            ondelete="CASCADE",
            onupdate="CASCADE"    
        ),
        index=True
    )
    url: Mapped[str] = mapped_column(String(128), nullable=False)
    quality: Mapped[str] = mapped_column(String, nullable=False)
    format: Mapped[str] = mapped_column(String, nullable=False)
    bitrate: Mapped[int] = mapped_column(Integer, nullable=False)
    codec: Mapped[str] = mapped_column(String, nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class Likes(Base):
    __tablename__ = "likes"

    video_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(
            "videos.id",
            ondelete="CASCADE",
            onupdate="CASCADE"    
        ),
        primary_key=True
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
            onupdate="CASCADE"    
        ),
        primary_key=True
    )
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=func.now())

    __table_args__ = (
        UniqueConstraint("video_id", "user_id"),
    )


class History(Base):
    __tablename__ = "history"

    video_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(
            "videos.id",
            ondelete="CASCADE",
            onupdate="CASCADE"    
        ),
        primary_key=True
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
            onupdate="CASCADE"    
        ),
        primary_key=True
    )
    watched_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=func.now())

    __table_args__ = (
        UniqueConstraint("video_id", "user_id"),
    )


class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
            onupdate="CASCADE" 
        )
    )
    expires_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    
class OauthAccount(Base):
    __tablename__ = "oauth_accounts"

    provider: Mapped[str] = mapped_column(
        String(64),
        primary_key=True
    )
    provider_user_id: Mapped[str] = mapped_column(
        String,
        primary_key=True
    )
    
    user_id: Mapped[int] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
            onupdate="CASCADE"    
        )
    )
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=func.now())
    
    __table_args__ = (
        PrimaryKeyConstraint("provider", "provider_user_id"),
    )

    
class AuthorSubscription(Base):
    __tablename__ = "author_subscriptions"

    id: Mapped[int] = mapped_column(primary_key=True)
    author_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        index=True,
    )
    days: Mapped[int] = mapped_column(Integer)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2))


# Once you confirm your subscription purchase, we record the presence of the subscription.
class UserSubscription(Base):
    __tablename__ = "user_subscriptions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        index=True,
    )
    author_subscription_id: Mapped[int] = mapped_column(
        ForeignKey("author_subscriptions.id"),
        index=True,
    )
    expires_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False
    )
    __table_args__ = (
        UniqueConstraint("user_id", "author_subscription_id"),
    )
    

# needed to create a label for the form so that the operation can be identified later
class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    author_subscription_id: Mapped[int] = mapped_column(ForeignKey("author_subscriptions.id"))

    status: Mapped[PaymentStatuses] = mapped_column(Enum(PaymentStatuses, native_enum=False))
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    
    provider_payment_id: Mapped[str | None] = mapped_column(nullable=True)

    created_at: Mapped[datetime.datetime] = mapped_column(default=datetime.datetime.utcnow)
    
    
class Balance(Base):
    __tablename__ = "balances"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0"))
    