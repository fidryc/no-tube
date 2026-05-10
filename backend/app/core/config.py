from pathlib import Path
from typing import Literal
from dotenv import load_dotenv
from pydantic_settings import BaseSettings


MODE: Literal["DEV", "PROD", "TEST"] = "DEV"

env_file = {
    "DEV": ".env.dev",
    "PROD": ".env.prod",
    "TEST": ".env.test",
}

class Settings(BaseSettings):
    LOG_LEVEL: Literal["INFO", "DEBUG", "WARNING", "ERROR"]

    DB_HOST: str
    DB_PORT: int
    DB_NAME: str
    DB_USER: str
    DB_PASS: str
    
    @property
    def DB_URL(self):
        if not self.__DB_URL:
            self.__DB_URL = f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        return self.__DB_URL
    
    RABBITMQ_HOST: str
    RABBITMQ_PORT: int
    RABBITMQ_USER: str
    RABBITMQ_PASS: str
    
    __RABBITMQ_URL = None
    @property
    def RABBITMQ_URL(self):
        if not self.__RABBITMQ_URL:
            self.__RABBITMQ_URL = f"amqp://{self.RABBITMQ_USER}:{self.RABBITMQ_PASS}@{self.RABBITMQ_HOST}:{self.RABBITMQ_PORT}/"
        return self.__RABBITMQ_URL
    
    REDIS_HOST: str
    REDIS_PORT: int
    REDIS_PASS: str
    
    # redis://[[username]:[password]@]host[:port][/db-number]
    __REDIS_URL = None
    @property
    def REDIS_URL(self):
        if not self.__REDIS_URL:
            self.__REDIS_URL = f"redis://{self.REDIS_USER}:{self.REDIS_PASS}@{self.REDIS_HOST}:{self.REDIS_PORT}"
        return self.__REDIS_URL
    
    SMTP_HOST: str
    SMTP_PORT: int
    SMTP_USER: str
    SMTP_PASS: str
    
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    
    YANDEX_CLIENT_ID: str
    YANDEX_CLIENT_SECRET: str
    
    AWS_ACCESS_KEY_ID: str
    AWS_SECRET_ACCESS_KEY: str
    ENDPOINT_URL: str
    REGION_NAME: str
    
    PRIVATE_BUCKET: str
    PUBLIC_BUCKET: str
    VIDEO_PROCESSIG_PREFIX: str
    PUBLIC_VIDEO_BASE_URL: str
    PUBLIC_VIDEO_PREFIX: str
    
    SECRET_NOTIFICATION: str
    SECRET_KEY_YOUKASSA: str
    SHOP_ID: int
    
    PRIVATE_VIDEO_PROXY_URL: str
    PRIVATE_VIDEO_PROXY_ENDPOINT: str
    __DB_URL = None
    __RABBITMQ_URL = None
    
    
    
    # __PRIVATE_SECRET_KEY = None
    # __PUBLIC_SECRET_KEY = None
    
    # @property
    # def PRIVATE_SECRET_KEY(self) -> str:
    #     if not self.__PRIVATE_SECRET_KEY:
    #         self.__PRIVATE_SECRET_KEY = Path(self.PRIVATE_SECRET_KEY_PATH).read_text()
    #     return self.__PRIVATE_SECRET_KEY
    
    # @property
    # def PUBLIC_SECRET_KEY(self) -> str:
    #     if not self.__PUBLIC_SECRET_KEY:
    #         self.__PUBLIC_SECRET_KEY = Path(self.PUBLIC_SECRET_KEY_PATH).read_text()
    #     return self.__PUBLIC_SECRET_KEY
    
    
    class Config:
        env_file = env_file[MODE]
        
def load_settings():
    load_dotenv(override=True)
    return Settings()
    
settings = load_settings()