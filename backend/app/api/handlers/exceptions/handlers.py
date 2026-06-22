from fastapi import HTTPException

from app.core.logger import logger

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.services.user import UserErrs, UserServiceException
from app.services.video import VideoErrs
from app.services.payment import PaymentErrs, PaymentServiceException


USER_SERVICE_STATUS_CODES = {
    UserErrs.ATTEMPT_LOGIN_OAUTH: 403,
    UserErrs.CACHE: 500,
    UserErrs.DB: 500,
    UserErrs.INVALID_DATA: 400,
    UserErrs.INVALID_PASSWORD: 400,
    UserErrs.TIME_TO_CONFIRM_EMAIL_EXPIRED: 400,
    UserErrs.UNKNOWN: 500,
    UserErrs.USER_ALREADY_EXISTS: 409,
    UserErrs.USER_NOT_EXISTS: 404,
    UserErrs.SESSION_EXPIRED: 401,
    UserErrs.SESSION_NOT_EXISTS: 401,
}

VIDEO_SERVICE_STATUS_CODES = {
    VideoErrs.INVALID_DATA: 400,
    VideoErrs.DB: 500,
    VideoErrs.CACHE: 500,
    VideoErrs.UNKNOWN: 500,
    VideoErrs.NO_RIGHTS: 403,
    VideoErrs.NOT_FOUND: 404,
    VideoErrs.SUBSCRIPTION_ALREADY_EXISTS: 409,
    VideoErrs.SUBSCRIPTION_EXPIRE: 403,
    VideoErrs.CANT_DELETE_LIKE: 422,
    VideoErrs.LIKE_EXISTS: 422,
    VideoErrs.SUBSCRIPTION_NOT_EXISTS: 403, 
    VideoErrs.BALANCE_NOT_EXISTS: 403,
}

PAYMENT_SERVICE_STATUS_CODES = {
    PaymentErrs.INVALID_DATA: 400,
    PaymentErrs.DB: 500,
    PaymentErrs.CACHE: 500,
    PaymentErrs.UNKNOWN: 500,
    PaymentErrs.NO_RIGHTS: 403,
    PaymentErrs.NO_FOUND: 404
}


def user_exc_handler(request: Request, exc: UserServiceException):
    status = USER_SERVICE_STATUS_CODES[exc.err]
    return JSONResponse(
        status_code=status,
        content={
            "error": {
                "code": exc.err,
                "message": str(exc) if status < 500 else "Internal server error",
                "details": None
            }
        }
    )
    
def video_exc_handler(request: Request, exc: UserServiceException):
    status = VIDEO_SERVICE_STATUS_CODES[exc.err]
    logger.info(msg=exc.args[0])
    return JSONResponse(
        status_code=status,
        content={
            "error": {
                "code": exc.err,
                "message": str(exc) if status < 500 else "Internal server error",
                "details": None
            }
        }
    )
    
def payment_exc_handler(request: Request, exc: PaymentServiceException):
    status = PAYMENT_SERVICE_STATUS_CODES[exc.err]
    logger.info(msg=exc.args[0])
    return JSONResponse(
        status_code=status,
        content={
            "error": {
                "code": exc.err,
                "message": str(exc) if status < 500 else "Internal server error",
                "details": None
            }
        }
    )
   
    
def validation_exc_handler(request: Request, exc: RequestValidationError):
    normalized = []
    for err in exc.errors():
        normalized.append(
            {
                "source": err["loc"][0],
                "field": ".".join(map(str, err["loc"][1:])),
                "message": err["msg"],
            }
        )
    
    content = {
        "error": {
            "code": "VALIDATION_ERROR",
            "message": "Validation failed",
            "details": normalized
        }
    }
    
    return JSONResponse(
        content=content,
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT
    )
    
def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        content={
            "error": {
                "code": "HTTP_EXCEPTION",
                "message": "HTTP_EXCEPTION",
                "details": exc.detail
            }
        },
        status_code=exc.status_code,
    )