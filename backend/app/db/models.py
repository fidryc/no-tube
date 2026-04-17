import datetime
import uuid
from sqlalchemy.orm import DeclarativeBase, mapped_column, Mapped, relationship
from sqlalchemy import Integer, PrimaryKeyConstraint, String, Boolean, ForeignKey, Enum, DateTime, Uuid, func
from typing import List

from app.domain.enums import ProcessingStatuses, Roles, Visibility


class Base(DeclarativeBase):
    pass

    
class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(64), nullable=False)
    email: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    hashed_password: Mapped[str] = mapped_column(String(256), nullable=True) # null because user can login with oauth2
    role: Mapped[Roles] = mapped_column(Enum(Roles, native_enum=False), index=True, nullable=False, default=Roles.USER)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=func.now())
    is_confirmed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, server_default="false")

class Video(Base):
    __tablename__ = "videos"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    description: Mapped[str] = mapped_column(String(512), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    processing_status: Mapped[ProcessingStatuses] = mapped_column(Enum(ProcessingStatuses, native_enum=False), nullable=False)
    visibility: Mapped[Visibility] = mapped_column(Enum(Visibility, native_enum=False), nullable=False, index=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=func.now())
    
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