from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError

from app.services.user import UserServiceException
from app.api.handlers.exceptions.handlers import user_exc_handler, validation_exc_handler

def add_exception_handlers(app: FastAPI):
    app.add_exception_handler(UserServiceException, user_exc_handler)
    app.add_exception_handler(RequestValidationError, validation_exc_handler)
    