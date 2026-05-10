import datetime
from typing import Optional
import uuid

from app.api.depends.cache import CacheDep
from app.api.depends.uow import UOWDepInit
from app.api.depends.user import get_user, get_user_if_exists
from app.domain.entitites import AuthorSubscriptionEntity, UserEntity, VideoEntity
from app.infrastructure.messages_broker.implementations.rabbitmq.producer import Producer
from app.infrastructure.s3.client import S3_CONFIG, S3Client
from app.schemas.schemas import AuthorSubscriptionResponse, IdResponse, LikeResponse, PaymentDataForFormResponse, StatusResponse, SubscriptionCheckResponse, SubscriptionIdResponse, SubscriptionSchema, UUIDResponse, UpdatePreviewSchema, UploadUrlPersignedResponse, UploadUrlResponse, UserResponseSchema, UserSubsResponse, VideoProcessingResponse, VideoResponseSchema, VideoSchema, VideoStatsResponse, VideoUpdateSchema

from fastapi import APIRouter, Depends, HTTPException, Response

from app.services.video import S3Service, VideoService
from app.core.config import settings
from app.services.payment import PaymentService
from app.domain.enums import ProcessingStatuses, Visibility
from app.api.depends.services import VideoServiceDep


router = APIRouter(
    prefix="/api/v1/videos",
    tags=["Videos"]
)
    
        
@router.post("/")
async def create(
    video: VideoSchema,
    video_service: VideoServiceDep,
    user: UserEntity = Depends(get_user)
) -> UUIDResponse:
    id = await video_service.create(user, video)
    return {"id": id}


@router.get("/")
async def get(
    video_service: VideoServiceDep,
    title: Optional[str] = None,
    user_id: Optional[int] = None,
    created_at: Optional[datetime.datetime] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> list[VideoResponseSchema]:
    videos = await video_service.get_with_filters(
        title,
        user_id,
        created_at,
        ProcessingStatuses.READY,
        [Visibility.PUBLIC, Visibility.SUBSCRIPTION],
        limit,
        offset
    )
    return videos

@router.post("/{id}/likes")
async def like(
    id: uuid.UUID,
    video_service: VideoServiceDep,
    user: UserEntity = Depends(get_user)
) -> UUIDResponse:
    id = await video_service.like(id, user.id)
    return {"id": id}

@router.delete("/{id}/likes")
async def delete_like(
    id: uuid.UUID,
    video_service: VideoServiceDep,
    user: UserEntity = Depends(get_user)
) -> UUIDResponse:
    id = await video_service.delete_like(id, user.id)
    return {"id": id}

@router.get("/{id}/likes")
async def is_liked(
    id: uuid.UUID,
    video_service: VideoServiceDep,
    user: UserEntity = Depends(get_user)
) -> LikeResponse:
    is_liked_flag = await video_service.is_liked(id, user.id)
    return LikeResponse(liked=is_liked_flag)

@router.post("/{id}/watch")
async def watch(
    id: uuid.UUID,
    video_service: VideoServiceDep,
    user: UserEntity = Depends(get_user)
):
    ids = await video_service.watch(id, user.id)
    

@router.post("/{id}/preview/upload-url")
async def preview_upload_url(
    id: uuid.UUID,
    video_service: VideoServiceDep,
    user: UserEntity = Depends(get_user)
) -> UploadUrlResponse:
    await video_service.validate_rights_for_change(id, user.id)

    client = S3Client(**S3_CONFIG)

    key = f"previews/videos/{id}.jpg"

    upload_url = await client.presigned_url_put(
        "no-tube-videos",
        key,
        3600
    )

    return {
        "upload_url": upload_url,
        "key": key
    }
    

@router.patch("/{id}/preview")
async def update_preview(
    id: uuid.UUID,
    data: UpdatePreviewSchema,
    video_service: VideoServiceDep,
    user: UserEntity = Depends(get_user)
) -> StatusResponse:
    s3_client = S3Client(**S3_CONFIG)
    await s3_client.check_exists_obj(settings.PUBLIC_BUCKET, data.preview_key)
    
    await video_service.update_preview(
        video_id=id,
        preview_key=data.preview_key,
        user_id=user.id
    )

    return {
        "status": "ok"
    }

@router.get("/me")
async def my_videos(
    video_service: VideoServiceDep,
    user: UserEntity = Depends(get_user),
) -> list[VideoResponseSchema]:
    return await video_service.get_with_filters(
        user_id=user.id
    )
    
@router.get("/me/subscriptions")
async def my_subscriptions(
    video_service: VideoServiceDep,
    user: UserEntity = Depends(get_user),
) -> UserSubsResponse:
    # TODO
    sub_ids = await video_service.subscriptions_user_ids(
        user_id=user.id
    )
    return {"sub_ids": sub_ids}
    
    
@router.get("/{id}/status")
async def video_status(
    id: uuid.UUID,
    video_service: VideoServiceDep,
) -> VideoProcessingResponse:
    video = await video_service.get_one(id)

    if not video:
        raise HTTPException(404)

    return {
        "processing_status": video.processing_status
    }

 
@router.get("/{id}")
async def get_one(
    id: uuid.UUID,
    video_service: VideoServiceDep,
    user: UserEntity = Depends(get_user_if_exists)
) -> VideoEntity:
    user_id = user.id if user else None
    await video_service.validate_rights_for_view(id, user_id)
    return await video_service.get_one(id)


@router.patch("/{id}")
async def update_video(
    id: uuid.UUID,
    data: VideoUpdateSchema,
    video_service: VideoServiceDep,
    user: UserEntity = Depends(get_user),
) -> StatusResponse:
    await video_service.update_video(
        video_id=id,
        user_id=user.id,
        title=data.title,
        description=data.description,
        visibility=data.visibility,
    )

    return {"status": "ok"}

@router.delete("/{id}")
async def delete_video(
    id: uuid.UUID,
    video_service: VideoServiceDep,
    user: UserEntity = Depends(get_user),
) -> StatusResponse:
    s3_client = S3Client(**S3_CONFIG)
    await video_service.delete_video(
        s3_client=s3_client,
        video_id=id,
        user_id=user.id,
    )

    return {"status": "deleted"}  
        
@router.post("/{id}/upload-url")
async def upload_url(
    id: uuid.UUID,
    video_service: VideoServiceDep,
    user: UserEntity = Depends(get_user)
) -> UploadUrlPersignedResponse:
    """Возвращаем ссылку на s3 объект для загрузки."""
    await video_service.validate_rights_for_change(id, user.id)
    client = S3Client(**S3_CONFIG)
    upload_url = await client.presigned_url_put("no-tube-videos", str(id), 3600)
    return {"upload_url": upload_url}

@router.get("/{id}/dash")
async def get_manifest(
    id: uuid.UUID,
    video_service: VideoServiceDep,
    user: UserEntity = Depends(get_user_if_exists)
):
    client = S3Client(**S3_CONFIG)
    s3_service = S3Service(client)
    user_id = user.id if user else None
    dash = await video_service.get_manifest(s3_service, id, user_id)
    return Response(
        content=dash,
        media_type="application/dash+xml",
        headers={"Cache-Control": "no-cache"}
    )
    
@router.get("/{id}/stats")
async def upload_url(
    id: uuid.UUID,
    video_service: VideoServiceDep,
    user: UserEntity = Depends(get_user)
) -> VideoStatsResponse:
    await video_service.validate_rights_for_view(id, user.id)
    stat = await video_service.get_stat(id)
    return {
        "likes": stat[0],
        "views": stat[1]
    }


@router.post("/{id}/process")
async def create_task_process_video(
    id: uuid.UUID,
    video_service: VideoServiceDep,
    user: UserEntity = Depends(get_user)
):
    await video_service.validate_rights_for_change(id, user.id)
    video = await video_service.get_one(id)
    client = S3Client(**S3_CONFIG)
    if not await client.check_exists_obj("no-tube-videos", str(id)):
        raise HTTPException(404)
    producer = Producer(settings.RABBITMQ_URL)
    async with producer:
        await producer.publish("video_process", {"video_name": str(id), "visibility": video.visibility}) 

@router.post("/subscriptions/authors/")
async def new_subscription(
    subscription_data: SubscriptionSchema,
    video_service: VideoServiceDep,
    user: UserEntity = Depends(get_user)
) -> IdResponse:
    sub_id = await video_service.create_subscription(
        user_id=user.id,
        days=subscription_data.days,
        price=subscription_data.price,
    )
    return {"id": sub_id}


@router.get("/subscriptions/authors/{author_id}")
async def get_sub_videos(
    author_id: int,
    video_service: VideoServiceDep,
) -> list[VideoEntity]:
    videos = await video_service.get_with_filters(
        user_id=author_id,
        visibility=Visibility.SUBSCRIPTION
    )
    return videos


@router.get("/subscriptions/authors/{author_id}/id")
async def get_sub_id(
    author_id: int,
    video_service: VideoServiceDep,
) -> SubscriptionIdResponse:
    id = await video_service.get_sub_id(author_id)
    return SubscriptionIdResponse(subscription_id=id)

@router.get("/subscriptions/{sub_id}")
async def get_sub_by_id(
    sub_id: int,
    video_service: VideoServiceDep,
) -> AuthorSubscriptionResponse:
    sub = await video_service.subscription_by_id(sub_id)
    return AuthorSubscriptionResponse(author_sub=sub)


@router.post("/subscriptions/authors/{sub_id}/payment")
async def payment(
    sub_id: int,
    uow: UOWDepInit,
    cache: CacheDep,
    video_service: VideoServiceDep,
    user: UserEntity = Depends(get_user),
) -> PaymentDataForFormResponse:
    data_for_form = await PaymentService(uow, cache, video_service).create_payment(user.id, sub_id)
    return data_for_form


@router.get("/subscriptions/authors/{sub_id}/check")
async def is_user_on_sub(
    sub_id: int,
    uow: UOWDepInit,
    cache: CacheDep,
    user: UserEntity = Depends(get_user)
) -> SubscriptionCheckResponse:
    is_subscribed = await VideoService(uow, cache).is_subscribed(user.id, sub_id)
    return {"is_subscribed": is_subscribed}

