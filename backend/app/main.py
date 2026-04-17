from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.logger import logger
from app.infrastructure.cache.impl.redis.redis import Cache
from app.api.v1.utils.include_routers import include_routers
from app.api.handlers.add_handlers import add_exception_handlers
from app.tasks.broker import broker
import taskiq_fastapi


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with Cache() as cache:
        logger.debug("Start app")
        app.state.cache = cache
        
        if not broker.is_worker_process:
            logger.debug("Starting broker")
            await broker.startup()
        yield
        if not broker.is_worker_process:
            logger.debug("Shutting down broker")
            await broker.shutdown()
        logger.debug("Close app")

app = FastAPI(lifespan=lifespan)

taskiq_fastapi.init(broker, "app.main:app")

include_routers(app=app)
add_exception_handlers(app=app)

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