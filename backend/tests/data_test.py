from app.repositories.implementations.sqlalchemy.repositories import UserRepository
from sqlalchemy.ext.asyncio import AsyncSession
import pytest


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "data,id",
    [
        ({"username": "test", "email": "test", "hashed_password": "test"}, 1),
        ({"username": "test", "email": "test2", "hashed_password": "test"}, 2),
        ({"username": "test", "email": "test2", "hashed_password": "test"}, 3)
    ]
)
async def test_insert(data: dict, id: int, session: AsyncSession):
    user_repo = UserRepository(session)
    assert await user_repo.add(data) == id
    
    
    