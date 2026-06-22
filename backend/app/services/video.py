import datetime
import decimal
from enum import Enum
import re
from time import timezone
from typing import Literal, Optional
import uuid

from app.db.models import Payment
from app.domain.entitites import AuthorSubscriptionEntity, UserEntity, VideoEntity, VideoStatsEntity, VideoWithUserSchema
from app.domain.enums import PaymentStatuses, ProcessingStatuses, Visibility
from app.infrastructure.cache.interface import ICache
from app.repositories.exceptions import BaseRepositoryException
from app.repositories.filter.enum import Operation
from app.repositories.filter.filter import And, Filter, Or
from app.repositories.interfaces.uow import IUOW
from app.schemas.schemas import UserResponseSchema, VideoResponseSchema, VideoResponseWithUserSchema, VideoSchema
from app.infrastructure.s3.client import S3Client
from app.utils.s3.url import build_url
from app.services.exception import BaseServiceException
from app.services.base_errs import BaseServiceErrs
from app.services.handler import get_handler
from app.core.config import settings
from app.core.logger import logger


PRIVATE_VIDEO_PROXY_URL = f"{settings.PRIVATE_VIDEO_PROXY_URL}/{settings.PRIVATE_VIDEO_PROXY_ENDPOINT}"
PUBLIC_VIDEO_BASE_URL = f"{settings.PUBLIC_VIDEO_BASE_URL}/{settings.PUBLIC_BUCKET}/{settings.PUBLIC_VIDEO_PREFIX}"

class S3Service:
    def __init__(self, S3_client: S3Client):
        self.S3_client = S3_client
        
    async def modify_manifest(self, base_url: str, manifest: str, video_id: uuid.UUID) -> str:
        base_url = f"{base_url}/{video_id}/"
    
        modified = re.sub(
            r'(<Period[^>]*>)',
            f'\\1\n\t\t<BaseURL>{base_url}</BaseURL>',
            manifest
        )
        
        return modified
    
    async def get_manifest(self, video_id: uuid.UUID) -> str:
        manifest = await self.S3_client.get_s3_file(settings.PRIVATE_BUCKET, f"processing/{video_id}/dash.mpd")
        return manifest
    
    
class VideoErrs(BaseServiceErrs):
    NO_RIGHTS = "NO_RIGHTS"
    NOT_FOUND = "NOT_FOUND"
    SUBSCRIPTION_ALREADY_EXISTS = "SUBSCRIPTION_ALREADY_EXISTS"
    SUBSCRIPTION_EXPIRE = "SUBSCRIPTION_EXPIRE"
    CANT_DELETE_LIKE = "CANT_DELETE_LIKE"
    LIKE_EXISTS = "LIKE_EXISTS"
    SUBSCRIPTION_NOT_EXISTS = "SUBSCRIPTION_NOT_EXISTS"
    BALANCE_NOT_EXISTS = "BALANCE_NOT_EXISTS"
    
    
class VideoServiceException(BaseServiceException):
    def __init__(self, *args, err: VideoErrs = BaseServiceErrs.UNKNOWN, **kwargs):
        super().__init__(*args, **kwargs)
        self.err = err
        

video_service_exc_handler = get_handler(VideoServiceException)

class VideoService:
    def __init__(self, uow: IUOW, cache: ICache):
        self.uow = uow
        self.cache = cache
        
    @video_service_exc_handler("VideoService.create")
    async def create(self, user: UserEntity, video: VideoSchema) -> str:
        id = await self.uow.video_repo.add(
            {
                "title": video.title,
                "description": video.description,
                "user_id": user.id,
                "processing_status": ProcessingStatuses.DRAFT,
                "visibility": Visibility.PRIVATE
            }
        )
        return str(id)
        
    @video_service_exc_handler("VideoService.change_status")
    async def change_status(self, video_id: int, new_status: ProcessingStatuses):
        await self.uow.video_repo.update_many(
            Filter("id", video_id, Operation.EQ),
            values={"processing_status": new_status}
        )
    
    @video_service_exc_handler("VideoService.validate_rights_for_view")  
    async def validate_rights_for_view(self, video_id: int, user_id: Optional[int]):
        video = await self.uow.video_repo.get_by_id(id=video_id)
        if not video: 
            raise VideoServiceException("Only the creator can receive a manifest.", err=VideoErrs.NOT_FOUND)
        
        if video.user_id == user_id:
            return 
        
        if video.visibility == Visibility.PUBLIC:
            return
        
        if video.visibility == Visibility.SUBSCRIPTION:
            if not user_id:
                raise VideoServiceException("Not found", err=VideoErrs.NOT_FOUND)
            author_id = video.user_id
            author_subscriptions = await self.uow.author_subscriptions_repo.get_by_filters(Filter("author_id", author_id, Operation.EQ))
            if not author_subscriptions:
                raise VideoServiceException("DB error", err=VideoErrs.DB)
            author_subscription_id = author_subscriptions[0].id
            
            subs = await self.uow.user_subscriptions_repo.get_by_filters(And(
                Filter("user_id", user_id, Operation.EQ),
                Filter("author_subscription_id", author_subscription_id, Operation.EQ),
            ))
            if not subs:
                # For security reasons, I don't show the user that there is such a video, but he doesn't have the rights.
                raise VideoServiceException("Not found", err=VideoErrs.NOT_FOUND)
            
            sub = subs[0]
            if datetime.datetime.now(datetime.timezone.utc) > sub.expires_at:
                raise VideoServiceException("Not found", err=VideoErrs.SUBSCRIPTION_EXPIRE)
            
            return
        
        if video.visibility == Visibility.PRIVATE and video.user_id != user_id:
            # For security reasons, I don't show the user that there is such a video, but he doesn't have the rights.
            raise VideoServiceException("Not found", err=VideoErrs.NOT_FOUND)
    
    @video_service_exc_handler("VideoService.create_subscription")    
    async def create_subscription(self, user_id: int, days: int, price: decimal.Decimal) -> int:
        if days < 0:
            raise VideoServiceException("Invalid days count", err=VideoErrs.INVALID_DATA)
        if price < 0:
            raise VideoServiceException("Invalid price", err=VideoErrs.INVALID_DATA)
        sub = await self.uow.author_subscriptions_repo.get_by_filters(
            And(
                Filter("author_id", user_id, Operation.EQ),
                Filter("days", days, Operation.EQ)
            )
        )
        if sub:
            raise VideoServiceException("Subscription already exists", err=VideoErrs.SUBSCRIPTION_ALREADY_EXISTS)
        sub_id = await self.uow.author_subscriptions_repo.add(
            {
                "author_id": user_id,
                "days": days,
                "price": price,
            }
        )
        
        balance = await self.uow.balance_repo.get_by_id(user_id, "user_id")
        if not balance:
            balance_id = await self.uow.balance_repo.add(
                {
                    "user_id": user_id,
                    "amount": 0,
                }
            )
        return sub_id
    
    @video_service_exc_handler("VideoService.subscribe")   
    async def subscribe(self, subscriber_id: int, subscription_id: int) -> int:
        subscription = await self.uow.author_subscriptions_repo.get_by_id(subscription_id)
        
        if not subscription:
            raise VideoServiceException("Sub not exists")
        user_subs = await self.uow.user_subscriptions_repo.get_by_filters(
            And(
                Filter("author_subscription_id", subscription_id),
                Filter("user_id", subscriber_id),
            )
        )
        
        # Если подписка есть, но время вышло - обновляем время подписки
        days = subscription.days
        if user_subs:
            user_sub = user_subs[0]
            start_sub_time = datetime.datetime.now(tz=datetime.timezone.utc)
            if user_sub.expires_at > start_sub_time:
                # Если подписка еще не закончилась - то продлеваем ее
                start_sub_time = user_sub.expires_at
            id = await self.uow.user_subscriptions_repo.update_many(
                And(
                    Filter("user_id", subscriber_id),
                    Filter("author_subscription_id", subscription_id),
                ),
                values={    
                    "expires_at": start_sub_time + datetime.timedelta(days=days)
                }
            )
            return id    
        
        # если подписки не существует, то создаем
        user_sub_id = await self.uow.user_subscriptions_repo.add(
            {
                "user_id": subscriber_id,
                "author_subscription_id": subscription_id,
                "expires_at": datetime.datetime.now(
                    tz=datetime.timezone.utc
                ) + datetime.timedelta(days=days),
            }
        )
        return user_sub_id
    
    @video_service_exc_handler("VideoService.get_with_filters")  
    async def get_with_filters(
        self,
        title: Optional[str] = None,
        user_id: Optional[int] = None,
        created_at: Optional[datetime.datetime] = None,
        processing_status: ProcessingStatuses = None,
        visibility: Optional[list[Visibility] | Visibility] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> list[VideoResponseWithUserSchema]:
        filters = []
        if processing_status:
            filters.append(
                Filter("processing_status", processing_status)
            )
        if visibility:
            if isinstance(visibility, list):
                fltrs = []
                for vs in visibility:
                    fltrs.append(
                        Filter("visibility", vs)
                    )
                filters.append(Or(*fltrs))
            else:
                filters.append(
                    Filter("visibility", visibility)
                )
        if title:
            filters.append(Filter("title", title))
        if user_id:
            filters.append(Filter("user_id", user_id))
        if created_at:
            filters.append(Filter("created_at", created_at, Operation.GE))
            
        videos = await self.uow.video_repo.get_by_filters_with_users(
            *filters,
            limit=limit,
            offset=offset,
            order_by_col_title="created_at",
            desc=True
        )
       
        videos_response = []
        for video in videos:
            videos_response.append(
                # You can check the video status, but I'll leave it like this for now.
                VideoResponseWithUserSchema(
                    id=video.id,
                    title=video.title,
                    description=video.description,
                    user_id=video.user_id,
                    processing_status=video.processing_status,
                    visibility=video.visibility,
                    created_at=video.created_at,
                    user=UserResponseSchema(
                        id = video.user.id,
                        username = video.user.username,
                        email = video.user.email,
                        created_at = video.user.created_at,
                        is_confirmed = video.user.is_confirmed,
                        avatar_url = build_url(video.user.avatar_key) if video.user.avatar_key else None,
                    ),
                    preview_url=build_url(video.preview_key) if video.preview_key and video.visibility != Visibility.PRIVATE else None,
                )
            )
        return videos_response
    
    @video_service_exc_handler("VideoService.get_one")  
    async def get_one(self, video_id: uuid.UUID) -> Optional[VideoEntity]:
        return await self.uow.video_repo.get_by_id(video_id)
    
    @video_service_exc_handler("VideoService.validate_rights_for_change")  
    async def validate_rights_for_change(self, video_id: uuid.UUID, user_id: int):
        video = await self.get_one(video_id)

        if not video:
            raise VideoServiceException(
                "Video not found",
                err=VideoErrs.NOT_FOUND
            )

        if video.user_id != user_id:
            raise VideoServiceException(
                "No rights",
                err=VideoErrs.NO_RIGHTS
            )
    
    @video_service_exc_handler("VideoService.validate_sub")
    async def validate_sub(self, user_id: int):
        if not await self.uow.author_subscriptions_repo.get_by_id(user_id, id_title_col="author_id"):
            raise VideoServiceException("Sub not exists", err = VideoErrs.SUBSCRIPTION_NOT_EXISTS)
        if not await self.uow.balance_repo.get_by_id(user_id, id_title_col="user_id"):
            raise VideoServiceException("balance not exists", err=VideoErrs.BALANCE_NOT_EXISTS) 
        
    @video_service_exc_handler("VideoService.update_video")
    async def update_video(
        self,
        video_id: uuid.UUID,
        user_id: int,
        title: Optional[str] = None,
        description: Optional[str] = None,
        visibility: Optional[Visibility] = None
    ):
        await self.validate_rights_for_change(video_id, user_id)

        values = {}

        if title is not None:
            values["title"] = title

        if description is not None:
            values["description"] = description

        if visibility is not None:
            if visibility == Visibility.SUBSCRIPTION:
                await self.validate_sub(user_id)
            values["visibility"] = visibility

        await self.uow.video_repo.update_many(
            Filter("id", video_id),
            values=values
        )
    
    @video_service_exc_handler("VideoService.delete_video")
    async def delete_video(
        self,
        s3_client: S3Client,
        video_id: uuid.UUID,
        user_id: int,
    ):
        await self.validate_rights_for_change(video_id, user_id)

        video = await self.get_one(video_id)
        await self.uow.video_repo.delete_by_filters(
            filters=[Filter("id", video_id, Operation.EQ)]
        )
        
        # delete from s3
        buckets = [settings.PRIVATE_BUCKET] # тк в приватном бакете всегда есть видео
        if video.visibility == Visibility.PUBLIC:
            buckets.append(settings.PUBLIC_BUCKET)
        for bucket in buckets:
            try:
                await s3_client.delete_with_prefix(
                    bucket,
                    f"{settings.VIDEO_PROCESSIG_PREFIX}/{str(video_id)}"
                )
            except Exception as e:
                logger.critical(
                    msg="Failed delete from s3",
                    exc_info=True,
                    extra={
                        "video_id": video_id,
                    }
                )                
    
    @video_service_exc_handler("VideoService.get_manifest")
    async def get_manifest(self, s3_service: S3Service, video_id: uuid.UUID, user_id: Optional[int]) -> str:
        video = await self.get_one(video_id)
        
        if not video:
            raise VideoServiceException(
                "Video not found",
                err=VideoErrs.NOT_FOUND
            )
        if video.processing_status != ProcessingStatuses.READY:
            raise VideoServiceException(
                "Video not ready",
                err=VideoErrs.NO_RIGHTS,
            )
        manifest_default = await s3_service.get_manifest(video_id)
        if video.visibility == Visibility.PUBLIC:
            manifest = await s3_service.modify_manifest(
                PUBLIC_VIDEO_BASE_URL,
                manifest_default,
                video_id
            )
            return manifest
        elif video.visibility == Visibility.PRIVATE or video.visibility == Visibility.SUBSCRIPTION:
            await self.validate_rights_for_view(video_id, user_id)
            manifest = await s3_service.modify_manifest(
                PRIVATE_VIDEO_PROXY_URL,
                manifest_default,
                video_id
            )
            return manifest
    
    @video_service_exc_handler("VideoService.is_liked")  
    async def is_liked(
        self,
        video_id: uuid.UUID,
        user_id: int,
    ) -> bool:
        likes = await self.uow.likes_repo.get_by_filters(
            Filter("video_id", video_id),
            Filter("user_id", user_id),
        )
        if not likes:
            return False
        return True
    
    @video_service_exc_handler("VideoService.like")  
    async def like(
        self,
        video_id: uuid.UUID,
        user_id: int,
    ) -> uuid.UUID:
        if await self.is_liked(video_id, user_id):
            raise VideoServiceException("Like already exists", err=VideoErrs.LIKE_EXISTS)
        ids = await self.uow.likes_repo.add(
            {
                "video_id": video_id,
                "user_id": user_id,
            },
            id_title_col=["video_id", "user_id"]
        )
        stat = await self.uow.video_stats_repo.get_by_id(video_id, "video_id")
        if not stat:
            await self.uow.video_stats_repo.add(
                {
                    "video_id": video_id,
                    "likes": 1,
                    "views": 0
                },
                "video_id"
            )
        else:
            await self.uow.video_stats_repo.update_many(
                Filter("video_id", video_id),
                values={
                    "video_id": video_id,
                    "likes": stat.likes + 1,
                    "views": stat.views
                },
                id_title_col="video_id"
            )
        return ids[0]
    
    @video_service_exc_handler("VideoService.delete_like")
    async def delete_like(
        self,
        video_id: uuid.UUID,
        user_id: int,
    ) -> uuid.UUID:
        if not await self.is_liked(video_id, user_id):
            raise VideoServiceException("Like not exists", err=VideoErrs.CANT_DELETE_LIKE)
        ids = await self.uow.likes_repo.delete_by_filters(
            filters=[
                Filter("video_id", video_id),
                Filter("user_id", user_id),
            ],
            id_title_col=["video_id", "user_id"],
        )
        
        stat = await self.uow.video_stats_repo.get_by_id(video_id, "video_id")
        await self.uow.video_stats_repo.update_many(
            Filter("video_id", video_id),
            values={
                "video_id": video_id,
                "likes": stat.likes - 1,
                "views": stat.views
            },
            id_title_col="video_id"
        )
        if ids:
            return ids[0][0]
          
    
    @video_service_exc_handler("VideoService.get_sub_id")    
    async def get_sub_id(self, author_id: int) -> Optional[uuid.UUID]:
        subs = await self.uow.author_subscriptions_repo.get_by_filters(Filter("author_id", author_id))
        
        if not subs:
            return None
        
        return subs[0].id
    
    @video_service_exc_handler("VideoService.watch")
    async def watch(self, video_id: uuid.UUID, user_id: int) -> tuple:
        if await self.uow.history_repo.get_by_id(
            [video_id, user_id],
            ["video_id", "user_id"]
        ):
            raise VideoServiceException("View exists", err=VideoErrs.INVALID_DATA)
        id = await self.uow.history_repo.add(
            {
                "video_id": video_id,
                "user_id": user_id,
            },
            id_title_col=["video_id", "user_id"],
        )
        # обновляем статистику 
        stat = await self.uow.video_stats_repo.get_by_id(video_id, "video_id")
        if not stat:
            await self.uow.video_stats_repo.add(
                {
                    "video_id": video_id,
                    "likes": 0,
                    "views": 1
                },
                "video_id"
            )
        else:
            ids = await self.uow.video_stats_repo.update_many(
                Filter("video_id", video_id),
                values={
                    "video_id": video_id,
                    "likes": stat.likes,
                    "views": stat.views + 1
                },
                id_title_col="video_id"
            )
        return id
    
    @video_service_exc_handler("VideoService.update_preview")   
    async def update_preview(
        self,
        video_id: uuid.UUID,
        preview_key: str,
        user_id: int,
    ):
        if not preview_key.startswith("previews/videos/") or len(preview_key.split("/")) != 3:
            raise VideoServiceException("Invalid preview key")
        await self.validate_rights_for_change(video_id, user_id)

        await self.uow.video_repo.update_many(
            Filter("id", video_id),
            values={
                "preview_key": preview_key
            }
        )
    
    @video_service_exc_handler("VideoService.get_stat")      
    async def get_stat(
        self,
        video_id: uuid.UUID
    ) -> tuple:
        # (likes, views)
        stat = await self.uow.video_stats_repo.get_by_id(video_id, "video_id")
        if stat:
            return (stat.likes, stat.views)
        return (0, 0)
    
    @video_service_exc_handler("VideoService.subscriptions_user")
    async def subscriptions_user_ids(self, user_id: int) -> list[int]:
        subs = await self.uow.user_subscriptions_repo.get_by_filters(
            Filter("user_id", user_id)
        )
        author_sub_ids = [sub.author_subscription_id for sub in subs]
        return author_sub_ids
    
    @video_service_exc_handler("VideoService.subscriptions_user")
    async def subscription_by_id(self, sub_id: int) -> AuthorSubscriptionEntity:
        sub = await self.uow.author_subscriptions_repo.get_by_id(sub_id)
        if not sub:
            raise VideoServiceException("Not found sub", err=VideoErrs.NOT_FOUND)
        return sub
        
    @video_service_exc_handler("VideoService.is_user_on_sub")
    async def is_subscribed(self, user_id: int, sub_id: int) -> bool:
        rows = await self.uow.user_subscriptions_repo.get_by_filters(
            Filter("author_subscription_id", sub_id),
            Filter("user_id", user_id)
        )
        if rows:
            return True
        return False