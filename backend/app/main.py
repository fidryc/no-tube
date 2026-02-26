from fastapi import FastAPI
from app.core.config import settings
from app.db.session import session_maker
from app.domain.enums import ProcessingStatuses, Visibility
from app.repositories.filter.enum import Operation
from app.repositories.filter.filter import And, Filter, Not, Or
from app.repositories.implementations.sqlalchemy.uow import UOW
from app.db.models import User

app = FastAPI()

@app.get("/")
async def test():
    async with UOW() as uow:
        try:
            print(await uow.user_repo.get_all())
        except Exception as e:
            print(e.args[0])
            
