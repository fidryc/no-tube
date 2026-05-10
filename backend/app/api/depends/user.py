from typing import Optional

from fastapi import Depends, HTTPException, Request

from app.api.constants import COOKIE_SESSION_ID
from app.api.depends.cache import CacheDep
from app.api.depends.uow import UOWDepInit
from app.domain.entitites import UserEntity
from app.services.user import UserService, UserServiceException
from app.api.handlers.exceptions.handlers import USER_SERVICE_STATUS_CODES


async def get_session_id(request: Request):
    return request.cookies.get(COOKIE_SESSION_ID, "")


async def get_user(uow: UOWDepInit, cache: CacheDep, session_id = Depends(get_session_id)) -> UserEntity:
    try:
        user_service = UserService(uow, cache)
        user = await user_service.authenticate_user(session_id)
        return user
    except UserServiceException as e:
        raise HTTPException(status_code=USER_SERVICE_STATUS_CODES[e.err], detail="Failed to get user")


async def get_user_if_exists(uow: UOWDepInit, cache: CacheDep, session_id = Depends(get_session_id)) -> Optional[UserEntity]:
    try:
        user_service = UserService(uow, cache)
        user = await user_service.authenticate_user(session_id)
        return user
    except UserServiceException as e:
        return None