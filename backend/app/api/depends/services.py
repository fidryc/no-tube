from typing import Annotated

from fastapi import Depends

from app.api.depends.cache import CacheDep
from app.api.depends.uow import UOWDepInit
from app.services.video import VideoService


async def get_video_service(uow: UOWDepInit, cache: CacheDep) -> VideoService:
    return VideoService(uow, cache)

VideoServiceDep = Annotated[VideoService, Depends(get_video_service)]