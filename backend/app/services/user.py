from datetime import datetime, timedelta, timezone
import secrets
from typing import Optional
from app.core.logger import logger

from app.domain.entitites import UserEntity
from app.domain.enums import Roles
from app.infrastructure.cache.exception import CacheException
from app.infrastructure.cache.interface import ICache
from app.repositories.exceptions import BaseRepositoryException
from app.repositories.interfaces.uow import IUOW
from app.schemas.schemas import UserSchemaLogin, UserSchemaRegister
from app.repositories.filter.filter import Filter, Operation
from app.utils.email.create_email import register_email
from app.utils.email.send import send_email
from app.utils.hashing import get_hash, check_pwd
from app.utils.oauth.get_user_data import GoogleUserInfo


class UserServiceException(Exception):
    def __init__(self, *args, status_code: int = 500, **kwargs):
        super().__init__(*args, **kwargs)
        self.status_code = status_code
        

CACHE_EX_SECONDS = 5
SESSION_EX_DAYS = 30

class UserService:
    def __init__(self, uow: IUOW, cache: ICache):
        self.uow = uow
        self.cache = cache
        
    async def create_user(self, user: UserSchemaRegister) -> int:
        """Creating a user from the registration form"""
        # Checking if a user does not exist
        if len(await self.uow.user_repo.get_by_filters(Filter("email", user.email, Operation.EQ))) > 0:
            raise UserServiceException("User already exists", status_code=409)
        
        # get a hashed password
        hashed_pwd = get_hash(user.password)
        
        data_user = {
            "username": user.username,
            "email": user.email,
            "hashed_password": hashed_pwd,
            "role": Roles.USER
        }
        try:
            user_id = await self.uow.user_repo.add(data_user)
            return user_id
        except BaseRepositoryException as e:
            raise UserServiceException("Error creating user", status_code=500) from e
            
    def create_session_data(self, session_id: str, user_id: int, expires_at: datetime) -> dict:
        if expires_at < datetime.now(timezone.utc):
            raise UserServiceException("Incorrect session expiration time", status_code=500)
        return {
            "id": session_id,
            "user_id": user_id,
            "expires_at": expires_at
        }
        
    def _to_flat(self, obj: dict) -> dict:
        new_obj = {}
        for k, v in obj.items():
            if isinstance(v, datetime):
                v = v.isoformat()
            new_obj[k] = v
        return new_obj
    
    def session_cache_key(self, session_id: str):
        return f"session:{session_id}"
        
    async def save_session_to_cache(self, session_data: dict):
        session_data_for_cache = self._to_flat(session_data)
        try:
            # Lifetime until the end of the session lifetime
            ttl = max(1, int((session_data.get("expires_at", datetime.now(timezone.utc)) - datetime.now(timezone.utc)).total_seconds()))
            await self.cache.dict_set(self.session_cache_key(session_data.get("id", "")), session_data_for_cache, ex=ttl)
        except CacheException as e:
            pass
        
    async def register(self, user: UserSchemaRegister) -> str:
        """Creates a user if valid data is passed in and returns the session ID"""
        user_id = await self.create_user(user)
        
        code = secrets.token_urlsafe(32)
        await self.send_verification_code(
            code=code,
            user_id=user_id,
            email_to=user.email
        )
        # TODO: отправка письма с кодом для подверждения
        
        session_id = await self.create_session(user_id=user_id)
        return session_id
    
    
    async def send_verification_code(self, code: str, user_id: int, email_to: str):
        # TODO: Сделать фоновой задачей
        try:
            SECONDS_FOR_REGISTER = 5 * 60
            await self.cache.set(f"code:{code}", user_id, ex=SECONDS_FOR_REGISTER)
            email = register_email("f98924746@gmail.com", code) # TODO: В продакшене поменять на email_to
            await send_email(email)
        except CacheException as e:
            logger.critical("Cache dropped. Unable to register.")
            raise UserServiceException("Please try registering later", status_code=500)
        
    
    async def confirm_email(self, code: str):
        user_id = None
        try:
            user_id = await self.cache.get(f"code:{code}")
        except CacheException as e:
            logger.critical("Cache dropped. Unable to confirm email.")
            raise UserServiceException("Please try confirm email later", status_code=500)
        
        if user_id and isinstance(user_id, str) and user_id.isdigit():
            user_id = int(user_id)
            try:
                await self.uow.user_repo.update(Filter("id", user_id, Operation.EQ), {"is_confirmed": True})
            except BaseRepositoryException as e:
                logger.error("Failed to update user", exc_info=True)
                raise UserServiceException("Failed to update user", status_code=500) from e
            logger.debug("Confirm email")
        else:
            raise UserServiceException("Please retry registration", status_code=408)
        
    @staticmethod
    def get_expire_session_time() -> datetime:  
        return datetime.now(timezone.utc) + timedelta(days=SESSION_EX_DAYS)
    
    
    async def create_session(self, user_id: int) -> str:
        session_id = secrets.token_urlsafe(32) 
        session_data = self.create_session_data(
            session_id,
            user_id,
            self.get_expire_session_time(),
        )

        try:
            await self.uow.session_repo.add(session_data)
        except BaseRepositoryException as e: 
            raise UserServiceException("Error creating session row", status_code=500) from e
        
        await self.save_session_to_cache(session_data)
        
        return session_id
    
     
    async def login(self, user: UserSchemaLogin) -> str:
        find_users = await self.uow.user_repo.get_by_filters(Filter("email", user.email, Operation.EQ))
        # Checking user exist
        if len(find_users) == 0:
            raise UserServiceException("Incorrect data entered", status_code=401)
        find_user = find_users[0]
        
        if find_user.hashed_password is None:
            raise UserServiceException("Login via Google or create a password", status_code=409)
        if not check_pwd(user.password, find_user.hashed_password):
            raise UserServiceException("Invalid password", status_code=401)
        
        return await self.create_session(find_user.id)
    
    async def change_password(self, user: UserEntity, new_password: str, old_password: str = None):
        if user.hashed_password is None:
            # for oauth
            await self.uow.user_repo.update(Filter("id", user.id, Operation.EQ), {"hashed_password": get_hash(new_password)})
            return
        elif old_password == new_password:
            raise UserServiceException("The new password must be different from the old one", status_code=400)
        
        if not check_pwd(old_password, user.hashed_password):
            raise UserServiceException("Incorrect old password.", status_code=401)
        
        await self.uow.user_repo.update(Filter("id", user.id, Operation.EQ), {"hashed_password": get_hash(new_password)})
        
    async def authenticate_user(self, session_id: str) -> UserEntity:
        session_data = None
        try:
            session_data = await self.cache.dict_get(self.session_cache_key(session_id))
        except CacheException as e:
            pass
        
        if session_data:
            # If there was data in the cache
            expires_at = datetime.fromisoformat(session_data["expires_at"])
            user_id = int(session_data["user_id"])
        else:
            try:
                session = await self.uow.session_repo.get_by_id(id=session_id)
            except BaseRepositoryException as e:
                raise UserServiceException("Failed get session from db", status_code=500) from e
            if not session:
                raise UserServiceException("You need to login to your account", status_code=401) # TODO: поменять логику работы исключений
            expires_at = session.expires_at
            user_id = session.user_id
            
            new_session_data_cache = self.create_session_data(session.id, user_id, expires_at)
            await self.save_session_to_cache(new_session_data_cache)
            
        if expires_at < datetime.now(timezone.utc):
            raise UserServiceException("You need to log in to your account", status_code=401)
        
        return await self.get_user(user_id)
        
    def user_cache_key(self, user_id: int) -> str:
        return f"user:{user_id}"
    
    def user_to_cache_data(self, user: UserEntity):
        return {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role.value,
            "created_at": user.created_at.isoformat(),
        }
        
    async def get_user(self, user_id: int) -> UserEntity:
        user_data: Optional[dict] = None
        try:
            user_data = await self.cache.dict_get(self.user_cache_key(user_id))
        except CacheException:
            pass
        
        if user_data:
            user_data["created_at"] = datetime.fromisoformat(user_data["created_at"])
            user_data["role"] = Roles[user_data["role"]]
            return UserEntity(**user_data)
        
        try:
            user = await self.uow.user_repo.get_by_id(user_id)
        except BaseRepositoryException as e:
            raise UserServiceException("Failed get user from db", status_code=500) from e
        
        if not user:
            raise UserServiceException("User not found", status_code=404)
        
        user_data = self.user_to_cache_data(user)
        try:
            await self.cache.dict_set(self.user_cache_key(user_id), user_data, ex=CACHE_EX_SECONDS)
        except CacheException as e:
            pass
        
        return user
    
    
    async def processing_google(self, google_user_info: GoogleUserInfo) -> str:
        """
            If the user obtained by id_token already exists in the system,
            then we'll create a session for this user.
            Otherwise, we'll create the user and return the session for them.
        """
        try:
            users_by_email = await self.uow.user_repo.get_by_filters(Filter("email", google_user_info.email, Operation.EQ))
        except BaseRepositoryException as e:
            logger.error("Failed to get user by email", exc_info=True)
            raise UserServiceException("Failed to get user by email", status_code=500) from e
        if len(users_by_email) > 0:
            user = users_by_email[0]
            # TODO: возможно добавить sub пользователю
            return await self.create_session(user_id=user.id)
        
        user_data = {
            "username": google_user_info.name,
            "email": google_user_info.email,
            "role": Roles.USER,
            "is_confirmed": google_user_info.email_verified
        }
        try:
            user_id = await self.uow.user_repo.add(
                user_data
            )
        except BaseRepositoryException as e:
            logger.error("Failed to create user", exc_info=True)
            raise UserServiceException("Failed add user", 500)
        
        return await self.create_session(user_id=user_id)
        