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
from app.repositories.filter.filter import And, Filter, Operation
from app.tasks.tasks.email import send_code_task
from app.utils.email.create_email import confirm_email
from app.utils.email.send import send_email
from app.utils.hashing import get_hash, check_pwd
from enum import Enum

class UserErrs(Enum):
    USER_ALREADY_EXISTS = "USER_ALREADY_EXISTS"
    USER_NOT_EXISTS = "USER_NOT_EXISTS"
    INVALID_DATA = "INVALID_DATA"
    TIME_TO_CONFIRM_EMAIL_EXPIRED = "TIME_TO_CONFIRM_EMAIL_EXPIRED"
    DB = "DB_ERROR"
    CACHE = "CACHE_ERROR"
    ATTEMPT_LOGIN_OAUTH = "ATTEMPT_LOGIN_OAUTH"
    INVALID_PASSWORD = "INVALID_PASSWORD"
    UNKNOW = "UNKNOW"
    SESSION_EXPIRED = "SESSION_EXPIRED"
    SESSION_NOT_EXISTS = "SESSION_NOT_EXISTS"
    
class UserServiceException(Exception):
    def __init__(self, *args, err: UserErrs = UserErrs.UNKNOW, **kwargs):
        super().__init__(*args, **kwargs)
        self.err = err
        
    
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
            raise UserServiceException("User already exists", err=UserErrs.USER_ALREADY_EXISTS)
        
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
            raise UserServiceException("Failed add user", err=UserErrs.DB) from e
            
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
        try:
            SECONDS_FOR_REGISTER = 5 * 60
            await self.cache.set(f"code:{code}", user_id, ex=SECONDS_FOR_REGISTER)
            await send_code_task.kiq("f98924746@gmail.com", code) # TODO: В продакшене поменять на email_to
        except CacheException as e:
            logger.critical("Cache dropped. Unable to register.")
            raise UserServiceException("Please try registering later", err=UserErrs.CACHE) from e
        
    
    async def confirm_email(self, code: str):
        user_id = None
        try:
            user_id = await self.cache.get(f"code:{code}")
        except CacheException as e:
            logger.critical("Cache dropped. Unable to confirm email.")
            raise UserServiceException("Please try confirm email later", err=UserErrs.CACHE)
        
        if user_id and isinstance(user_id, str) and user_id.isdigit():
            user_id = int(user_id)
            try:
                await self.uow.user_repo.update(Filter("id", user_id, Operation.EQ), {"is_confirmed": True})
            except BaseRepositoryException as e:
                logger.error("Failed to update user", exc_info=True)
                raise UserServiceException("Failed to update user", err=UserErrs.DB) from e
            logger.debug("Confirm email")
        else:
            raise UserServiceException("Please retry confirm email", err=UserErrs.TIME_TO_CONFIRM_EMAIL_EXPIRED)
        
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
            raise UserServiceException("Error creating session row", err=UserErrs.DB) from e
        
        await self.save_session_to_cache(session_data)
        
        return session_id
    
     
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
    
    async def change_password(self, user: UserEntity, new_password: str, old_password: str = None):
        if user.hashed_password is None:
            # for oauth
            await self.uow.user_repo.update(Filter("id", user.id, Operation.EQ), {"hashed_password": get_hash(new_password)})
            return
        elif old_password == new_password:
            raise UserServiceException("The new password must be different from the old one", err=UserErrs.INVALID_PASSWORD)
        
        if not check_pwd(old_password, user.hashed_password):
            raise UserServiceException("Incorrect old password.", err=UserErrs.INVALID_PASSWORD)
        
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
                raise UserServiceException("Failed get session from db", err=UserErrs.DB) from e
            if not session:
                raise UserServiceException("You need to login to your account", err=UserErrs.SESSION_NOT_EXISTS) # TODO: поменять логику работы исключений
            expires_at = session.expires_at
            user_id = session.user_id
            
            new_session_data_cache = self.create_session_data(session.id, user_id, expires_at)
            await self.save_session_to_cache(new_session_data_cache)
            
        if expires_at < datetime.now(timezone.utc):
            raise UserServiceException("You need to log in to your account", err=UserErrs.SESSION_EXPIRED)
        
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
            "is_confirmed": str(int(user.is_confirmed)) # возможен трабл с типом
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
            user_data["is_confirmed"] = bool(int(user_data["is_confirmed"]))
            return UserEntity(**user_data)
        
        try:
            user = await self.uow.user_repo.get_by_id(user_id)
        except BaseRepositoryException as e:
            raise UserServiceException("Failed get user from db", err=UserErrs.DB) from e
        
        if not user:
            raise UserServiceException("User not found", err=UserErrs.USER_NOT_EXISTS)
        
        user_data = self.user_to_cache_data(user)
        try:
            await self.cache.dict_set(self.user_cache_key(user_id), user_data, ex=CACHE_EX_SECONDS)
        except CacheException as e:
            pass
        
        return user
    
    
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
        try:
            oauth_accounts = await self.uow.oauth_account_repo.get_by_filters(
                And(
                    Filter("provider", provider, Operation.EQ),
                    Filter("provider_user_id", sub, Operation.EQ),
                )
            )
        except BaseRepositoryException as e:
            raise UserServiceException("Failed to get oauth account", err=UserErrs.DB) from e
        if oauth_accounts:
            # Если oauth найден - получаем user_id 
            oauth_account = oauth_accounts[0]
            return await self.create_session(user_id=oauth_account.user_id)
        
        
        # Если такого oauth аккаунта нет - Пытаемся найти пользователя в системе
        try:
            users = await self.uow.user_repo.get_by_filters(
                Filter("email", email, Operation.EQ)
            )
        except BaseRepositoryException as e:
            raise UserServiceException("Failed to get user by email") from e
           
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
            try:
                user_id = await self.uow.user_repo.add(
                    user_data
                )
            except BaseRepositoryException as e:
                raise UserServiceException("Failed add user", err=UserErrs.DB) from e

        # После получения user_id - можем создать oauth аккаунт
        
        oauth_account_data = {
            "provider": provider,
            "provider_user_id": sub,
            "user_id": user_id
        }
        try:
            await self.uow.oauth_account_repo.add(oauth_account_data, id_title_col=None)
        except BaseRepositoryException as e:
            raise UserServiceException("Failed add oauth_account", err=UserErrs.DB) from e
        
        return await self.create_session(user_id=user_id)
        