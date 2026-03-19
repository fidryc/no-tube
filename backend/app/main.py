from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.api.depends.cache import CacheDep
from app.core.logger import logger
from app.infrastructure.cache.impl.redis.redis import Cache
from app.infrastructure.cache.interface import ICache
from app.repositories.implementations.sqlalchemy.uow import UOW
from app.api.v1.user_router import router as user_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with Cache() as cache:
        logger.debug("Start app")
        app.state.cache = cache
        yield
        logger.debug("Close app")

app = FastAPI(lifespan=lifespan)

app.include_router(user_router)

origins = [
    "http://localhost:5173",
    "https://frontend-app.com" # TODO: change in production
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # The list of allowed origins
    allow_credentials=True, # Allow cookies to be sent cross-origin
    allow_methods=["*"],    # Allow all methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],    # Allow all headers
)

@app.get("/")
async def test(cache: CacheDep):
    await cache.set("key", "dfd", 10)
    print(await cache.get("key"))
