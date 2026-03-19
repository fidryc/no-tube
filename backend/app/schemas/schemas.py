from pydantic import BaseModel

class UserSchemaRegister(BaseModel):
    username: str
    email: str
    password: str
    

class UserSchemaLogin(BaseModel):
    email: str
    password: str