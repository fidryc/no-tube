from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError

from app.services.user import UserServiceException
from app.api.handlers.exceptions.handlers import http_exception_handler, user_exc_handler, validation_exc_handler, video_exc_handler
from app.services.video import VideoServiceException

def add_exception_handlers(app: FastAPI):
    app.add_exception_handler(UserServiceException, user_exc_handler)
    app.add_exception_handler(VideoServiceException, video_exc_handler)
    app.add_exception_handler(RequestValidationError, validation_exc_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)