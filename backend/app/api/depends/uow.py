from contextlib import asynccontextmanager
from typing import Annotated, AsyncGenerator

from fastapi import Depends

from app.api.depends.session import SessionDep
from app.repositories.implementations.sqlalchemy.uow import UOW

async def get_uow_init() -> AsyncGenerator[UOW, None]:
    async with UOW() as uow:
        yield uow

UOWDepInit = Annotated[UOW, Depends(get_uow_init)]

from typing import AsyncGenerator, Callable
from fastapi import Depends

def get_uow_init_with_isolation_level(isolation_level: str):
    async def dependency():
        async with UOW(isolation_level) as uow:
            yield uow
    return dependency

