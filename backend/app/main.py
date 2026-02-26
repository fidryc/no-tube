from operator import or_

from fastapi import FastAPI
from sqlalchemy import Select, and_, or_
from app.core.config import settings
from app.db.session import session_maker
from app.domain.enums import ProcessingStatuses, Visibility
from app.repositories.filter.enum import Operation
from app.repositories.filter.impl.sqlalchemy.filter import And, Filter, Or
from app.repositories.implementations.sqlalchemy.uow import UOW
from app.db.models import User

app = FastAPI()

@app.get("/")
async def test():
    async with UOW() as uow:
        try:
            print(
                await uow.video_repo.get_by_filters(
                    Or(
                        And(
                            Filter("visibility", Visibility.PUBLIC, Operation.EQ),
                            Filter("user_id", 4, Operation.EQ)
                        ),
                        And(
                            Filter("title", "Travel Vlog", Operation.EQ),
                            Filter("visibility", Visibility.PRIVATE, Operation.EQ)
                        )
                    )
                )
            )
            print(
                await uow.video_repo.get_by_filters(
                    And(
                        Filter("processing_status", ProcessingStatuses.PROCESSING, Operation.EQ),
                        Or(
                            Filter("id", 1, Operation.EQ),
                            And(
                                Filter("visibility", Visibility.PUBLIC, Operation.EQ),
                                Or(
                                    Filter("user_id", 5, Operation.EQ),
                                    Filter("user_id", 7, Operation.EQ)
                                )
                            )
                        )
                    )
                )
            )
            print(
                await uow.video_repo.get_by_filters(
                    Or(
                        Filter("title", "Funny Cats Compilation", Operation.EQ),
                        Filter("title", "Cooking Tips", Operation.EQ),
                        And(
                            Filter("visibility", Visibility.PRIVATE, Operation.EQ),
                            Filter("user_id", 6, Operation.EQ)
                        )
                    )
                )
            )
            print(
                await uow.video_repo.get_by_filters(
                    And(
                        Filter("processing_status", ProcessingStatuses.PROCESSING, Operation.EQ),
                        Or(
                            Filter("visibility", Visibility.PUBLIC, Operation.EQ),
                            Filter("user_id", 6, Operation.EQ)
                        )
                    )
                )
            )
            print(
                await uow.video_repo.get_by_filters(
                    Or(
                        And(
                            Filter("id", 1, Operation.EQ),
                            Filter("visibility", Visibility.PUBLIC, Operation.EQ)
                        ),
                        And(
                            Filter("id", 2, Operation.EQ),
                            Filter("visibility", Visibility.PUBLIC, Operation.EQ)
                        ),
                        And(
                            Filter("id", 3, Operation.EQ),
                            Filter("visibility", Visibility.PRIVATE, Operation.EQ)
                        )
                    )
                )
            )
        except Exception as e:
            print(e.args[0])
            