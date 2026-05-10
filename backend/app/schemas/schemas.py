import datetime
import decimal
from typing import Optional
import uuid

from pydantic import BaseModel, Field, field_validator, model_validator, EmailStr
import re

from app.domain.enums import ProcessingStatuses, Visibility
from app.domain.entitites import AuthorSubscriptionEntity

class UserSchemaRegister(BaseModel):
    username: str = Field(min_length=8)
    email: EmailStr
    password: str
    
    @field_validator("password")
    @classmethod
    def password_validator(cls, password: str):
        msg_errs = []
        if len(password) < 8:
            msg_errs.append("Password must be at least 8 characters long")
        if len(re.findall(r"\d", password)) < 3:
            msg_errs.append("Password must contain at least 3 digits")
        if not re.search(r"[A-Za-z]", password):
            msg_errs.append("Password must contain at least one letter")
        
        if not msg_errs:
            return password
        raise ValueError("; ".join(msg_errs))
    
    @model_validator(mode="after")
    def check_passwords_match(self):
        if self.password == self.email:
            raise ValueError("Password must not be the same as email")
        return self
    

class UserSchemaLogin(BaseModel):
    email: str
    password: str
    
class UserResponseSchema(BaseModel):
    id: int
    username: str
    email: str
    created_at: datetime.datetime
    is_confirmed: bool
    avatar_url: Optional[str] = None

class VideoSchema(BaseModel):
    title: str
    description: str

class VideoUpdateSchema(BaseModel):
    title: str
    description: str
    visibility: Visibility
    
class VideoResponseSchema(BaseModel):
    id: uuid.UUID
    title: str
    description: str
    user_id: int
    processing_status: ProcessingStatuses
    visibility: Visibility
    created_at: datetime.datetime
    preview_url: Optional[str] = None
    
class SubscriptionSchema(BaseModel):
    days: int = Field(gt=0)
    price: float = Field(gt=0)
    
class UpdatePreviewSchema(BaseModel):
    preview_key: str
    
class StatusResponse(BaseModel):
    status: str
    
class IdResponse(BaseModel):
    id: int
    
class UUIDResponse(BaseModel):
    id: uuid.UUID
    
class LikeResponse(BaseModel):
    liked: bool
    
class UploadUrlResponse(BaseModel):
    upload_url: str
    key: str
    
class UserSubsResponse(BaseModel):
    sub_ids: list[int]
    
class VideoProcessingResponse(BaseModel):
    processing_status: str
    
class UploadUrlPersignedResponse(BaseModel):
    upload_url: str
    
class VideoStatsResponse(BaseModel):
    likes: int
    views: int
    
class SubscriptionIdResponse(BaseModel):
    subscription_id: Optional[int]
    
class AuthorSubscriptionResponse(BaseModel):
    author_sub: Optional[AuthorSubscriptionEntity]
    
class PaymentDataForFormResponse(BaseModel):
    payment_id: uuid.UUID 
    price: decimal.Decimal
    
class SubscriptionCheckResponse(BaseModel):
    is_subscribed: bool
    
class YandexParamsResponse(BaseModel):
    client_id: str
    response_type: str
    redirect_uri: str
    
class ConfirmationTokenResponse(BaseModel):
    confirmation_token: str
    
    