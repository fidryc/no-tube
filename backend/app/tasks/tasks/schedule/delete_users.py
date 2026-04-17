from app.repositories.exceptions import BaseRepositoryException
from app.repositories.filter.enum import Operation
from app.tasks.broker import broker
from app.db.session import async_session_maker
from app.repositories.implementations.sqlalchemy.repositories import UserRepository
from app.repositories.filter.filter import Filter, And
from datetime import datetime, timedelta, timezone
from app.core.logger import logger


@broker.task(schedule=[{"cron": "0 2 * * *"}]) # 0 2 * * *
async def delete_users():
    async with async_session_maker() as session:
        user_repo = UserRepository(session)
        time_boundary = datetime.now(timezone.utc) - timedelta(hours=10)
        try:
            await user_repo.delete_by_filters(
                filters=[And(
                    Filter("is_confirmed", False, Operation.EQ),
                    Filter("created_at", time_boundary, Operation.LE)
                )]
            )
        except BaseRepositoryException as e:
            logger.debug("Error deleting users with unverified email addresses")
            
        await session.commit()