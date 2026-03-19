from typing import Any

from redis import RedisError

from app.infrastructure.cache.exception import CacheException
from app.infrastructure.cache.interface import ICache
import redis.asyncio as redis
from app.core.logger import logger

class Cache(ICache):
    def __init__(self):
        self._connection = None
        
    async def __aenter__(self):
        # TODO: Дописать конфиг
        # TODO: Дописать обработку исключений
        self._connection = redis.Redis(
            decode_responses=True,
            socket_connect_timeout=0.2,
            socket_timeout=0.2,
            retry_on_timeout=False,
            health_check_interval=0
        )
        
        try:
            await self._connection.ping()
        except RedisError as e:
            raise CacheException("Error connecting to redis") from e
        
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            logger.info(
                msg="Redis error",
                exc_info=True
            )
        if self._connection is not None:
            try:
                await self._connection.close()
            except redis.RedisError as e:
                logger.critical(
                    msg="Redis closing error",
                    exc_info=True
                )
                raise CacheException("Redis closing error") from e
            
            
    async def get(self, key: str) -> Any:
        if self._connection is not None:
            try:
                return await self._connection.get(key)
            except redis.RedisError as e:
                logger.critical(
                    msg="Redis get error",
                    exc_info=True,
                    extra={
                        "key": key
                    }
                )
                raise CacheException("Redis get error") from e
            except Exception as e:
                raise CacheException("Redis get error") from e

    async def set(self, key: str, value: Any, ex: int):
        if self._connection:
            try:
                await self._connection.set(
                    name=key,
                    value=value,
                    ex=ex
                )
            except redis.RedisError as e:
                logger.critical(
                    msg="Redis set error",
                    exc_info=True,
                    extra={
                        "key": key,
                        "value": value,
                        "ex": ex
                    }
                )
                raise CacheException("Redis set error") from e
            except Exception as e:
                raise CacheException("Redis set error") from e
            
    async def dict_set(self, key: str, value: dict, ex: int | None = None):
        if self._connection:
            try:
                await self._connection.hset(name=key, mapping=value)
            except redis.RedisError as e:
                logger.critical(
                    msg="Redis hset error",
                    exc_info=True,
                    extra={
                        "key": key,
                        "value": value,
                        "ex": ex
                    }
                )
                raise CacheException("Redis hset error") from e
            except Exception as e:
                raise CacheException("Redis hset error") from e
            
            if ex:
                try:
                    await self._connection.expire(name=key, time=ex)
                except redis.RedisError as e:
                    logger.critical(
                        msg="Redis hset error",
                        exc_info=True,
                        extra={"ex": ex}
                    )
                    raise CacheException("Redis set ex error") from e
                except Exception as e:
                    raise CacheException("Redis set ex error") from e
        
    async def dict_get(self, key: str) -> dict:
        if self._connection:
            try:
                return await self._connection.hgetall(name=key)
            except redis.RedisError as e:
                logger.critical(
                    msg="Redis hgetall error",
                    exc_info=True,
                    extra={"key": key}
                )
                raise CacheException("Redis hgetall error") from e
            except Exception as e:
                raise CacheException("Redis hgetall error") from e
        
    async def dict_get_field(self, key: str, field: str):
        if self._connection:
            try:
                return await self._connection.hget(name=key, key=field)
            except redis.RedisError as e:
                logger.critical(
                    msg="Redis hgetall error",
                    exc_info=True,
                    extra={"key": key, "field": field}
                )
                raise CacheException("Redis hgetall error") from e
            except Exception as e:
                raise CacheException("Redis hgetall error") from e
            
    async def dict_delete(self, key: str):
        if self._connection:
            try:
                await self._connection.delete(key)
            except redis.RedisError as e:
                logger.critical(
                    msg="Redis delete error",
                    exc_info=True,
                    extra={"key": key}
                )
                raise CacheException("Redis delete error") from e