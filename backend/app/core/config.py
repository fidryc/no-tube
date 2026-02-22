from pathlib import Path
from typing import Literal
from dotenv import load_dotenv
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    MODE: Literal["DEV", "PROD", "TEST"]
    
    LOG_LEVEL: Literal["INFO", "DEBUG", "WARNING", "ERROR"]

    DB_HOST: str
    DB_PORT: int
    DB_NAME: str
    DB_USER: str
    DB_PASS: str

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
    
    PRIVATE_SECRET_KEY_PATH: str
    PUBLIC_SECRET_KEY_PATH: str
    
    __DB_URL = None
    
    @property
    def DB_URL(self):
        if not self.__DB_URL:
            DB_URLS = {
                "TEST": f"postgresql+asyncpg://{self.TEST_DB_USER}:{self.TEST_DB_PASS}@{self.TEST_DB_HOST}:{self.TEST_DB_PORT}/{self.TEST_DB_NAME}",
                "PROD": f"postgresql+asyncpg://{self.PROD_DB_USER}:{self.PROD_DB_PASS}@{self.PROD_DB_HOST}:{self.PROD_DB_PORT}/{self.PROD_DB_NAME}",
                "DEV": f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}",
            }
            self.__DB_URL = DB_URLS[self.MODE]
        return self.__DB_URL
    
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