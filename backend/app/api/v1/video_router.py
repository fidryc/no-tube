from app.api.depends.cache import CacheDep
from app.api.depends.uow import UOWDepInit
from app.api.depends.user import get_user
from app.domain.entitites import UserEntity
from app.infrastructure.messages_broker.implementations.rabbitmq.producer import Producer
from app.infrastructure.s3.client import S3_CONFIG, S3Client
from app.schemas.schemas import VideoSchema

from fastapi import APIRouter, Depends

from app.services.video import VideoService
from app.core.logger import logger
from app.core.config import settings


router = APIRouter(
    prefix="/api/v1/video",
    tags=["Videos"]
)
    
        
@router.post("/")
async def create(video: VideoSchema, uow: UOWDepInit, cache: CacheDep, user: UserEntity = Depends(get_user)) -> str:
    id = await VideoService(uow, cache).create(user, video)
    return id
    
    
@router.put("/{id}/status")
async def change_Status(new_status: str, uow: UOWDepInit, cache: CacheDep):
    """Смена статуса видео"""
    await VideoService(uow, cache).change_status(new_status)
   
        
@router.post("/{id}/upload-url")
async def upload_url(id: str):
    """Возвращаем ссылку на s3 объект для загрузки."""
    client = S3Client(**S3_CONFIG)
    return await client.generate_presigned_url_put("no-tube-videos", id, 3600)


@router.get("/put_object")
async def put_object(id: str):
    client = S3Client(**S3_CONFIG)
    with open("oranguta-pointing-finger.mp4", "rb") as file:
        if await client.check_exists_obj("no-tube-videos", "FDFDFF"):
            print("Существует")
            return
        print( await client.put_data("no-tube-videos", file.name, file.read()))


@router.get("/task/process")
async def create_task_process_video(video_name: str, visibility: str, uow: UOWDepInit, cache: CacheDep, user: UserEntity = Depends(get_user)):
    # TODO: проверка файла
    # client = S3Client(**S3_CONFIG)
    # if not await client.check_exists_obj("no-tube-videos", video_name):
    #     return
    producer = Producer(settings.RABBITMQ_URL)
    async with producer:
        await producer.publish("video_process", {"video_name": video_name, "visibility": visibility})
    