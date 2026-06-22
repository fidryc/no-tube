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
from app.schemas.schemas import UserResponseSchema, UserSchemaLogin, UserSchemaRegister
from app.repositories.filter.filter import And, Filter, Operation
from app.tasks.tasks.email import send_code_task
from app.utils.email.create_email import confirm_email
from app.utils.email.send import send_email
from app.utils.hashing import get_hash, check_pwd
from enum import Enum

from app.services.video import VideoServiceException
from app.utils.s3.url import build_url
from app.services.base_errs import BaseServiceErrs
from app.services.exception import BaseServiceException
from app.services.handler import get_handler

class UserErrs(BaseServiceErrs):
    USER_ALREADY_EXISTS = "USER_ALREADY_EXISTS"
    USER_NOT_EXISTS = "USER_NOT_EXISTS"
    TIME_TO_CONFIRM_EMAIL_EXPIRED = "TIME_TO_CONFIRM_EMAIL_EXPIRED"
    ATTEMPT_LOGIN_OAUTH = "ATTEMPT_LOGIN_OAUTH"
    INVALID_PASSWORD = "INVALID_PASSWORD"
    SESSION_EXPIRED = "SESSION_EXPIRED"
    SESSION_NOT_EXISTS = "SESSION_NOT_EXISTS"
    NOT_FOUND = "NOT_FOUND"
    
class UserServiceException(BaseServiceException):
    def __init__(self, *args, err: UserErrs = BaseServiceErrs.UNKNOWN, **kwargs):
        super().__init__(*args, **kwargs)
        self.err = err
        
    
CACHE_EX_SECONDS = 60*6
SESSION_EX_DAYS = 30

user_service_exc_handler = get_handler(UserServiceException)

class UserService:
    def __init__(self, uow: IUOW, cache: ICache):
        self.uow = uow
        self.cache = cache
    
    @user_service_exc_handler("UserService.create_user")  
    async def create_user(self, user: UserSchemaRegister) -> int:
        """Creating a user from the registration form"""
        # Checking if a user does not exist
        if len(await self.uow.user_repo.get_by_filters(Filter("email", user.email, Operation.EQ))) > 0:
            raise UserServiceException("User already exists", err=UserErrs.USER_ALREADY_EXISTS)
        
        # get a hashed password
        hashed_pwd = get_hash(user.password)
        
        data_user = {
            "username": user.username,
            "email": user.email,
            "hashed_password": hashed_pwd,
            "role": Roles.USER
        }
        
        user_id = await self.uow.user_repo.add(data_user)
        return user_id
        
    def create_session_data(self, session_id: str, user_id: int, expires_at: datetime) -> dict:
        if expires_at < datetime.now(timezone.utc):
            raise UserServiceException("Invalid expires_at", err=UserErrs.INVALID_DATA)
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
        
    @user_service_exc_handler("UserService.register")
    async def register(self, user: UserSchemaRegister) -> str:
        """Creates a user if valid data is passed in and returns the session ID"""
        user_id = await self.create_user(user)
        
        code = secrets.token_urlsafe(32)
        await self.send_verification_code(
            code=code,
            user_id=user_id,
            email_to=user.email
        )
        
        session_id = await self.create_session(user_id=user_id)
        return session_id
    
    
    async def send_verification_code(self, code: str, user_id: int, email_to: str):
        try:
            SECONDS_FOR_REGISTER = 5 * 60
            await self.cache.set(f"code:{code}", user_id, ex=SECONDS_FOR_REGISTER)
            await send_code_task.kiq("f98924746@gmail.com", code) # TODO: В продакшене поменять на email_to
        except CacheException as e:
            logger.critical("Cache dropped. Unable to register.")
            raise UserServiceException("Please try registering later", err=UserErrs.CACHE) from e
        
    @user_service_exc_handler("UserService.confirm_email")
    async def confirm_email(self, code: str):
        user_id = None
        try:
            user_id = await self.cache.get(f"code:{code}")
        except CacheException as e:
            logger.critical("Cache dropped. Unable to confirm email.")
            raise UserServiceException("Please try confirm email later", err=UserErrs.CACHE)
        
        if user_id and isinstance(user_id, str) and user_id.isdigit():
            user_id = int(user_id)
            await self.uow.user_repo.update_many(Filter("id", user_id, Operation.EQ), {"is_confirmed": True})
            logger.debug("Confirm email")
        else:
            raise UserServiceException("Please retry confirm email", err=UserErrs.TIME_TO_CONFIRM_EMAIL_EXPIRED)
        
    @staticmethod
    def get_expire_session_time() -> datetime:  
        return datetime.now(timezone.utc) + timedelta(days=SESSION_EX_DAYS)
    
    @user_service_exc_handler("UserService.create_session")
    async def create_session(self, user_id: int) -> str:
        session_id = secrets.token_urlsafe(32) 
        session_data = self.create_session_data(
            session_id,
            user_id,
            self.get_expire_session_time(),
        )

        await self.uow.session_repo.add(session_data)
        
        await self.save_session_to_cache(session_data)
        
        return session_id
    
    @user_service_exc_handler("UserService.login")
    async def login(self, user: UserSchemaLogin) -> str:
        find_users = await self.uow.user_repo.get_by_filters(Filter("email", user.email, Operation.EQ))
        # Checking user exist
        if len(find_users) == 0:
            raise UserServiceException("Incorrect data entered", err=UserErrs.USER_NOT_EXISTS)
        find_user = find_users[0]
        
        if find_user.hashed_password is None:
            raise UserServiceException("Login via Google or create a password", err=UserErrs.ATTEMPT_LOGIN_OAUTH)
        if not check_pwd(user.password, find_user.hashed_password):
            raise UserServiceException("Invalid password", err=UserErrs.INVALID_DATA)
        
        return await self.create_session(find_user.id)
    
    @user_service_exc_handler("UserService.change_password")
    async def change_password(self, user: UserEntity, new_password: str, old_password: str = None):
        if user.hashed_password is None:
            # for oauth
            await self.uow.user_repo.update_many(Filter("id", user.id, Operation.EQ), {"hashed_password": get_hash(new_password)})
            return
        elif old_password == new_password:
            raise UserServiceException("The new password must be different from the old one", err=UserErrs.INVALID_PASSWORD)
        
        if not check_pwd(old_password, user.hashed_password):
            raise UserServiceException("Incorrect old password.", err=UserErrs.INVALID_PASSWORD)
        
        await self.uow.user_repo.update_many(Filter("id", user.id, Operation.EQ), {"hashed_password": get_hash(new_password)})
        await self.cache.dict_delete(self.user_cache_key(user.id))
    
    @user_service_exc_handler("UserService.authenticate_user")   
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
            session = await self.uow.session_repo.get_by_id(id=session_id)
            if not session:
                raise UserServiceException("You need to login to your account", err=UserErrs.SESSION_NOT_EXISTS) # TODO: поменять логику работы исключений
            expires_at = session.expires_at
            user_id = session.user_id
            
            new_session_data_cache = self.create_session_data(session.id, user_id, expires_at)
            await self.save_session_to_cache(new_session_data_cache)
            
        if expires_at < datetime.now(timezone.utc):
            raise UserServiceException("You need to log in to your account", err=UserErrs.SESSION_EXPIRED)
        
        return await self.get_user(user_id)
    
    async def get_by_id(self, user_id: int) -> UserResponseSchema:
        user = await self.uow.user_repo.get_by_id(user_id)
        if not user:
            raise UserServiceException("Not found user", err=UserErrs.USER_NOT_EXISTS)
        user = self.convert_user_to_response(user)
        return user
        
    @classmethod
    def convert_user_to_response(cls, user: UserEntity) -> UserResponseSchema:
        return UserResponseSchema(
            id = user.id,
            username = user.username,
            email = user.email,
            created_at = user.created_at,
            is_confirmed = user.is_confirmed,
            avatar_url = build_url(user.avatar_key) if user.avatar_key else None,
        )
        
    def user_cache_key(self, user_id: int) -> str:
        return f"user:{user_id}"
    
    def user_to_cache_data(self, user: UserEntity):
        data = {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role.value,
            "created_at": user.created_at.isoformat(),
            "is_confirmed": str(int(user.is_confirmed)), # возможен трабл с типом
            "avatar_key": user.avatar_key,  
        }
        if user.hashed_password:
            data["hashed_password"] = user.hashed_password
        if user.avatar_key:
            data["avatar_key"] = user.avatar_key
        return data
    
    @user_service_exc_handler("UserService.get_user")    
    async def get_user(self, user_id: int) -> UserEntity:
        user_data: Optional[dict] = None
        try:
            user_data = await self.cache.dict_get(self.user_cache_key(user_id))
        except CacheException:
            pass
        
        if user_data:
            user_data["id"] = int(user_data["id"])
            user_data["created_at"] = datetime.fromisoformat(user_data["created_at"])
            user_data["role"] = Roles[user_data["role"]]
            user_data["is_confirmed"] = bool(int(user_data["is_confirmed"]))
            return UserEntity(**user_data)
        
        user = await self.uow.user_repo.get_by_id(user_id)
        
        if not user:
            raise UserServiceException("User not found", err=UserErrs.USER_NOT_EXISTS)
        
        user_data = self.user_to_cache_data(user)
        try:
            await self.cache.dict_set(self.user_cache_key(user_id), user_data, ex=CACHE_EX_SECONDS)
        except CacheException as e:
            pass
        
        return user
    
    @user_service_exc_handler("UserService.processing_oauth_account")
    async def processing_oauth_account(
        self,
        sub: str,
        provider: str,
        email: str,
        is_confirmed: bool = False,
        username: Optional[str] = None
    ) -> str:
        # TODO: перевести коменты
        """
            If the user obtained by id_token already exists in the system,
            then we'll create a session for this user.
            Otherwise, we'll create the user and return the session for them.
        """
        
        oauth_accounts = await self.uow.oauth_account_repo.get_by_filters(
            And(
                Filter("provider", provider, Operation.EQ),
                Filter("provider_user_id", sub, Operation.EQ),
            )
        )
        if oauth_accounts:
            # Если oauth найден - получаем user_id 
            oauth_account = oauth_accounts[0]
            return await self.create_session(user_id=oauth_account.user_id)
        
        
        # Если такого oauth аккаунта нет - Пытаемся найти пользователя в системе
        
        users = await self.uow.user_repo.get_by_filters(
            Filter("email", email, Operation.EQ)
        )
           
        user_id = None
        if users:
            # Если пользователь есть - то надо привязать аккаунт к нему
            user_id = users[0].id
        else:
            # Иначе создадим пользователя и получим id
            user_data = {
                "username": username if username else email,
                "email": email,
                "role": Roles.USER,
                "is_confirmed": is_confirmed
            }
            # TODO: возможно стоит отправлять сразу письмо с подверждением если is_confirmed - false
            
            user_id = await self.uow.user_repo.add(
                user_data
            )

        # После получения user_id - можем создать oauth аккаунт
        
        oauth_account_data = {
            "provider": provider,
            "provider_user_id": sub,
            "user_id": user_id
        }
        await self.uow.oauth_account_repo.add(oauth_account_data, id_title_col=None)
        
        return await self.create_session(user_id=user_id)
    
    @user_service_exc_handler("UserService.update_key_avatar")
    async def update_key_avatar(self, avatar_key: str, user_id: int) -> int:
        if not avatar_key.startswith("avatars/users/") or avatar_key.split("/")[-1].split(".")[-2] != str(user_id):
            raise UserServiceException("Incorrect key avatar", err=UserErrs.INVALID_DATA)
        id = await self.uow.user_repo.update_many(
            Filter("id", user_id),
            {
                "avatar_key": avatar_key
            }
        )
        await self.cache.dict_delete(self.user_cache_key(user_id))
        return id
        