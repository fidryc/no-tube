from enum import Enum

from app.domain.entitites import UserEntity
from app.domain.enums import ProcessingStatuses, Visibility
from app.infrastructure.cache.interface import ICache
from app.repositories.exceptions import BaseRepositoryException
from app.repositories.filter.enum import Operation
from app.repositories.filter.filter import Filter
from app.repositories.interfaces.uow import IUOW
from app.schemas.schemas import VideoSchema


class VideoErrs(Enum):
    INVALID_DATA = "INVALID_DATA"
    DB = "DB_ERROR"
    CACHE = "CACHE_ERROR"
    UNKNOW = "UNKNOW"
    
class VideoServiceException(Exception):
    def __init__(self, *args, err: VideoErrs = VideoErrs.UNKNOW, **kwargs):
        super().__init__(*args, **kwargs)
        self.err = err

class VideoService:
    def __init__(self, uow: IUOW, cache: ICache):
        self.uow = uow
        self.cache = cache
        
    async def create(self, user: UserEntity, video: VideoSchema) -> str:
        try:
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
        except BaseRepositoryException as e:
            raise VideoServiceException("Faied create video", err=VideoErrs.DB) from e
        

    async def change_status(self, video_id: int, new_status: ProcessingStatuses):
        try:
            await self.uow.video_repo.update(
                Filter("id", video_id, Operation.EQ),
                values={"processing_status": new_status}
            )
        except BaseRepositoryException as e:
            raise VideoServiceException("Failed change status", err=VideoErrs.DB) from e