from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.services.user import UserErrs, UserServiceException


USER_SERVICE_STATUS_CODES = {
    UserErrs.ATTEMPT_LOGIN_OAUTH: 403,
    UserErrs.CACHE: 500,
    UserErrs.DB: 500,
    UserErrs.INVALID_DATA: 400,
    UserErrs.INVALID_PASSWORD: 400,
    UserErrs.TIME_TO_CONFIRM_EMAIL_EXPIRED: 400,
    UserErrs.UNKNOW: 500,
    UserErrs.USER_ALREADY_EXISTS: 409,
    UserErrs.USER_NOT_EXISTS: 404,
    UserErrs.SESSION_EXPIRED: 401,
    UserErrs.SESSION_NOT_EXISTS: 401,
}


def user_exc_handler(request: Request, exc: UserServiceException):
    status = USER_SERVICE_STATUS_CODES[exc.err]
    return JSONResponse(
        status_code=status,
        content={
            "error": {
                "code": exc.err.value,
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