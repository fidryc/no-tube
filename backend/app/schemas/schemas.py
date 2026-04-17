from pydantic import BaseModel, Field, field_validator, model_validator, EmailStr
import re

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
    

class VideoSchema(BaseModel):
    title: str
    description: str