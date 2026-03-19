from fastapi import Depends, Request
from typing import Annotated

from app.infrastructure.cache.impl.redis.redis import Cache

async def get_cache(request: Request) -> Cache:
    return request.app.state.cache

CacheDep = Annotated[Cache, Depends(get_cache)]