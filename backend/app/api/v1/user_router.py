import asyncio
from math import e
from typing import Annotated

import aio_pika
from fastapi import APIRouter, Body, Depends, HTTPException, Request, Response
from fastapi.responses import JSONResponse, RedirectResponse

from app.api.constants import COOKIE_SESSION_ID
from app.api.depends.cache import CacheDep
from app.api.depends.uow import UOWDepInit
from app.api.depends.user import get_user
from app.domain.entitites import UserEntity
from app.infrastructure.messages_broker.implementations.rabbitmq.producer import Producer
from app.schemas.schemas import UserSchemaLogin, UserSchemaRegister
from app.services.user import SESSION_EX_DAYS, UserErrs, UserService, UserServiceException
from app.utils.oauth.google.generate_url import generate_oauth_redirect_url
from app.utils.oauth.google.get_user_data import get_user_info
from app.repositories.filter.enum import Operation
from app.utils.hashing import get_hash
from app.repositories.filter.filter import Filter
from app.api.depends.session import SessionDep
from app.db.models import User
from app.utils.oauth.yandex.get_query_params import get_query_params
from app.utils.oauth.yandex.get_user_data import get_yandex_user_data

router = APIRouter(
    prefix="/api/v1/user",
    tags=["Users"]
)


SECONDS_IN_DAY = 60 * 60 * 24
SESSION_EX_SECONDS = SECONDS_IN_DAY * SESSION_EX_DAYS


@router.post("/register")
async def register(user: UserSchemaRegister, uow: UOWDepInit, cache: CacheDep, response: Response):
    # TODO: добавить валидацию для почты
    session_id = await UserService(uow, cache).register(user)
    response.set_cookie(COOKIE_SESSION_ID, session_id, max_age=SESSION_EX_SECONDS) # TODO: Изменить настройки безопасности


@router.post("/login")
async def login(user: UserSchemaLogin, uow: UOWDepInit, cache: CacheDep, response: Response):
    session_id = await UserService(uow, cache).login(user)
    response.set_cookie(COOKIE_SESSION_ID, session_id, max_age=SESSION_EX_SECONDS) # TODO: Изменить настройки безопасности | Сделать одиннаковое время в кеше и в куках
        
        
@router.get("/confirm")
async def confirm(token: str, uow: UOWDepInit, cache: CacheDep):
    await UserService(uow, cache).confirm_email(token)
    
        
@router.post("/quit")
async def quit(response: Response):
    response.delete_cookie(COOKIE_SESSION_ID)


# @router.post("/delete")
# async def delete(uow: UOWDepInit, cache: CacheDep, user: UserEntity = Depends(get_user)):


@router.get("/me")
async def authentication(user: UserEntity = Depends(get_user)):
    return {
        "username": user.username,
        "email": user.email,
        "role": user.role
    } # TODO поменять на схему

    
@router.patch("/change_password")
async def change_password(uow: UOWDepInit, cache: CacheDep, user: UserEntity = Depends(get_user), old_password: str = Body(), new_password: str = Body()):
    await UserService(uow, cache).change_password(user, old_password=old_password, new_password=new_password)
    

@router.get("/google/url")
async def url_google():
    return RedirectResponse(url=generate_oauth_redirect_url())


@router.post("/google/callback")
async def callback_google(code: Annotated[str, Body(embed=True)], uow: UOWDepInit, cache: CacheDep, response: Response):
    google_user_info = await get_user_info(code)
    session_id = await UserService(uow, cache).processing_oauth_account(
        sub=google_user_info.sub,
        provider="google",
        email=google_user_info.email,
        is_confirmed=google_user_info.email_verified
    )
    response.set_cookie(COOKIE_SESSION_ID, session_id, max_age=SESSION_EX_SECONDS) # TODO сделать одиннаковое время
    
    
@router.get("/yandex/query_params")
async def query_params_yandex() -> dict:
    return get_query_params()


@router.post("/yandex/callback")
async def yandex_callback(access_token: Annotated[str, Body(embed=True)], uow: UOWDepInit, cache: CacheDep, response: Response):
    try:
        user = await get_yandex_user_data(access_token)
    except ValueError as e:
        raise HTTPException("Invalid token", 422)
    
    session_id = await UserService(uow, cache).processing_oauth_account(
        sub=user.provider_id,
        provider="yandex",
        email=user.email,
        is_confirmed=user.is_confirmed,
        username=user.username if user.username else None
    )
    response.set_cookie(COOKIE_SESSION_ID, session_id, max_age=SESSION_EX_SECONDS)