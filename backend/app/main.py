from fastapi import FastAPI
from app.core.config import settings
from app.db.session import session_maker
from app.repositories.implementations.sqlalchemy.repositories import UserRepository
from app.repositories.implementations.sqlalchemy.uow import UOW
app = FastAPI()