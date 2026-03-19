from typing import Annotated, AsyncGenerator

from fastapi import Depends

from app.api.depends.session import SessionDep
from app.repositories.implementations.sqlalchemy.uow import UOW

async def get_uow_init() -> AsyncGenerator[UOW, None]:
    async with UOW() as uow:
        yield uow

UOWDepInit = Annotated[UOW, Depends(get_uow_init)]
