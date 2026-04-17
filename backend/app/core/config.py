from pathlib import Path
from typing import Literal
from dotenv import load_dotenv
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    MODE: Literal["DEV", "PROD", "TEST"]
    
    LOG_LEVEL: Literal["INFO", "DEBUG", "WARNING", "ERROR"]

    DEV_DB_HOST: str
    DEV_DB_PORT: int
    DEV_DB_NAME: str
    DEV_DB_USER: str
    DEV_DB_PASS: str

    TEST_DB_HOST: str
    TEST_DB_PORT: int
    TEST_DB_NAME: str
    TEST_DB_USER: str
    TEST_DB_PASS: str

    PROD_DB_HOST: str
    PROD_DB_PORT: int
    PROD_DB_NAME: str
    PROD_DB_USER: str
    PROD_DB_PASS: str
    
    DEV_RABBITMQ_HOST: str
    DEV_RABBITMQ_PORT: int
    DEV_RABBITMQ_USER: str
    DEV_RABBITMQ_PASS: str

    TEST_RABBITMQ_HOST: str
    TEST_RABBITMQ_PORT: int
    TEST_RABBITMQ_USER: str
    TEST_RABBITMQ_PASS: str

    PROD_RABBITMQ_HOST: str
    PROD_RABBITMQ_PORT: int
    PROD_RABBITMQ_USER: str
    PROD_RABBITMQ_PASS: str
    
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
    
    __DB_URL = None
    __RABBITMQ_URL = None
    
    @property
    def DB_URL(self):
        if not self.__DB_URL:
            DB_URLS = {
                "TEST": f"postgresql+asyncpg://{self.TEST_DB_USER}:{self.TEST_DB_PASS}@{self.TEST_DB_HOST}:{self.TEST_DB_PORT}/{self.TEST_DB_NAME}",
                "PROD": f"postgresql+asyncpg://{self.PROD_DB_USER}:{self.PROD_DB_PASS}@{self.PROD_DB_HOST}:{self.PROD_DB_PORT}/{self.PROD_DB_NAME}",
                "DEV": f"postgresql+asyncpg://{self.DEV_DB_USER}:{self.DEV_DB_PASS}@{self.DEV_DB_HOST}:{self.DEV_DB_PORT}/{self.DEV_DB_NAME}",
            }
            self.__DB_URL = DB_URLS[self.MODE]
        return self.__DB_URL
    
    @property
    def RABBITMQ_URL(self):
        if not self.__DB_URL:
            URLS = {
                "TEST": f"amqp://{self.TEST_RABBITMQ_USER}:{self.TEST_RABBITMQ_PASS}@{self.TEST_RABBITMQ_HOST}:{self.TEST_RABBITMQ_PORT}/",
                "PROD": f"amqp://{self.PROD_RABBITMQ_USER}:{self.PROD_RABBITMQ_PASS}@{self.PROD_RABBITMQ_HOST}:{self.PROD_RABBITMQ_PORT}/",
                "DEV": f"amqp://{self.DEV_RABBITMQ_USER}:{self.DEV_RABBITMQ_PASS}@{self.DEV_RABBITMQ_HOST}:{self.DEV_RABBITMQ_PORT}/"
            }
            self.__RABBITMQ_URL = URLS[self.MODE]
        return self.__RABBITMQ_URL
    
    __PRIVATE_SECRET_KEY = None
    __PUBLIC_SECRET_KEY = None
    
    @property
    def PRIVATE_SECRET_KEY(self) -> str:
        if not self.__PRIVATE_SECRET_KEY:
            self.__PRIVATE_SECRET_KEY = Path(self.PRIVATE_SECRET_KEY_PATH).read_text()
        return self.__PRIVATE_SECRET_KEY
    
    @property
    def PUBLIC_SECRET_KEY(self) -> str:
        if not self.__PUBLIC_SECRET_KEY:
            self.__PUBLIC_SECRET_KEY = Path(self.PUBLIC_SECRET_KEY_PATH).read_text()
        return self.__PUBLIC_SECRET_KEY
        
    class Config:
        env_file = ".env"
        
def load_settings():
    load_dotenv(override=True)
    return Settings()
    
settings = load_settings()