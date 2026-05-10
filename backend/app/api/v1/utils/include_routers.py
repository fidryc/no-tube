from fastapi import FastAPI

from app.api.v1.user_router import router as user_router
from app.api.v1.video_router import router as video_router
from app.api.v1.payment_router import router as payment_router

def include_routers(app: FastAPI):
    app.include_router(user_router)
    app.include_router(video_router)
    app.include_router(payment_router)