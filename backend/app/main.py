from operator import or_

from fastapi import FastAPI
from sqlalchemy import Select, and_, or_
from app.core.config import settings
from app.db.session import session_maker
from app.domain.enums import ProcessingStatuses, Visibility
from app.repositories.filter.enum import Operation
from app.repositories.filter.impl.sqlalchemy.filter import And, Filter, Not, Or
from app.repositories.implementations.sqlalchemy.uow import UOW
from app.db.models import User

app = FastAPI()

@app.get("/")
async def test():
    async with UOW() as uow:
        try:
            # 1️⃣ Получить все видео, кроме с id <= 3
            print("\n--- Test 1: NOT id <= 3 ---")
            videos = await uow.video_repo.get_by_filters(Not(Filter("id", 3, Operation.LE)))
            print(videos)

            # 2️⃣ Получить видео с id = 1 или user_id >= 6
            print("\n--- Test 2: OR(id=1, user_id>=6) ---")
            videos = await uow.video_repo.get_by_filters(
                Or(
                    Filter("id", 1, Operation.EQ),
                    Filter("user_id", 6, Operation.GE)
                )
            )
            print(videos)

            # 3️⃣ Видео с id = 3 и title = "Travel Vlog"
            print("\n--- Test 3: AND(id=3, title='Travel Vlog') ---")
            videos = await uow.video_repo.get_by_filters(
                And(
                    Filter("id", 3, Operation.EQ),
                    Filter("title", "Travel Vlog", Operation.EQ)
                )
            )
            print(videos)

            # 4️⃣ Сложная вложенная комбинация
            print("\n--- Test 4: OR(id=1, AND(title='Travel Vlog', user_id>=6)) ---")
            videos = await uow.video_repo.get_by_filters(
                Or(
                    Filter("id", 1, Operation.EQ),
                    And(
                        Filter("title", "Travel Vlog", Operation.EQ),
                        Filter("user_id", 6, Operation.GE)
                    )
                )
            )
            print(videos)
        except Exception as e:
            print(e.args[0])
            
