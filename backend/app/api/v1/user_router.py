from math import e
from typing import Annotated

from fastapi import APIRouter, Body, Depends, HTTPException, Response
from fastapi.responses import RedirectResponse
from sqlalchemy import Select, Update, text

from app.api.constants import COOKIE_SESSION_ID
from app.api.depends.cache import CacheDep
from app.api.depends.uow import UOWDepInit
from app.api.depends.user import get_user
from app.domain.entitites import UserEntity
from app.schemas.schemas import UserSchemaLogin, UserSchemaRegister
from app.services.user import SESSION_EX_DAYS, UserService, UserServiceException
from app.utils.oauth.generate_url import generate_oauth_redirect_url
from app.utils.oauth.get_user_data import get_user_info
from app.repositories.filter.enum import Operation
from app.utils.hashing import get_hash
from app.repositories.filter.filter import Filter
from app.api.depends.session import SessionDep
from app.db.models import User

router = APIRouter(
    prefix="/v1/user",
    tags=["Users"]
)

SECONDS_IN_DAY = 60 * 60 * 24
SESSION_EX_SECONDS = SECONDS_IN_DAY * SESSION_EX_DAYS

@router.post("/register")
async def register(user: UserSchemaRegister, uow: UOWDepInit, cache: CacheDep, response: Response):
    # добавить валидацию для почты
    session_id = await UserService(uow, cache).register(user)
    response.set_cookie(COOKIE_SESSION_ID, session_id, max_age=SESSION_EX_SECONDS) # TODO: Изменить настройки безопасности

# TODO: изменить методы post
@router.post("/login")
async def login(user: UserSchemaLogin, uow: UOWDepInit, cache: CacheDep, response: Response):
    session_id = await UserService(uow, cache).login(user)
    response.set_cookie(COOKIE_SESSION_ID, session_id, max_age=SESSION_EX_SECONDS) # TODO: Изменить настройки безопасности | Сделать одиннаковое время в кеше и в куках
        
@router.get("/confirm")
async def login(token: str, uow: UOWDepInit, cache: CacheDep):
    await UserService(uow, cache).confirm_email(token)
        
@router.post("/quit")
async def quit():
    pass

@router.post("/delete")
async def delete():
    pass

@router.post("/authentication")
async def authentication(user: UserEntity = Depends(get_user)):
    return {
        "username": user.username,
        "email": user.email,
        "role": user.role
    } # TODO поменять на схему
    
    
@router.patch("/change_password")
async def change_password(uow: UOWDepInit, cache: CacheDep, user: UserEntity = Depends(get_user), old_password: str = Body(), new_password: str = Body()):
    try:
        await UserService(uow, cache).change_password(user, old_password=old_password, new_password=new_password)
    except UserServiceException as e:
        raise HTTPException(status_code=e.status_code, detail="Failed to get user by email")


@router.get("/google/url")
async def url_google():
    return RedirectResponse(url=generate_oauth_redirect_url())


@router.post("/google/callback")
async def callback_google(code: Annotated[str, Body(embed=True)], uow: UOWDepInit, cache: CacheDep, response: Response):
    google_user_info = await get_user_info(code)
    try:
        session_id = await UserService(uow, cache).processing_google(google_user_info)
    except UserServiceException as e:
        raise HTTPException(status_code=e.status_code, detail="Failed to get user by email")
    response.set_cookie(COOKIE_SESSION_ID, session_id, max_age=SESSION_EX_SECONDS) # TODO сделать одиннаковое время
    