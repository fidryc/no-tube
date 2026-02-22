from sqlalchemy import Delete, Select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import DeclarativeBase
from app.repositories.exceptions import BaseRespositoryException
from app.repositories.implementations.sqlalchemy.utils.converters import to_dict
from app.repositories.interfaces.base_repository import IRepository
from sqlalchemy.ext.asyncio import AsyncSession
from typing import TypeVar
from app.core.logger import logger
from app.utils.mapper import mapping_to_obj


DEFAULT_ERROR_DESCRIPTION = "Unknow error in db"

Model = TypeVar("Model", bound=DeclarativeBase)
Entity = TypeVar("Entity")

class Repository(IRepository[Model, Entity]):
    model: Model = None
    entity: Entity
    
    def __init__(self, session: AsyncSession):
        self.session = session
        
    async def get_by_id(self, id: int) -> Entity | None:
        if not self.model:
            raise BaseRespositoryException("The method cannot work without a model")
        query = Select(self.model).where(self.model.id == id)
        try:
            obj = (await self.session.execute(query)).scalars().one_or_none()
            try:
                print(obj)
                print(to_dict(obj))
                ent = mapping_to_obj(to_dict(obj), self.entity)
                return ent
            except Exception as e:
                logger.critical(
                    "Failed to convert to entity",
                    exc_info=True,
                    extra={"obj": obj.__dict__}
                )
        except SQLAlchemyError as e:
            logger.critical(
                msg="Error getting data from method 'get_by_id'",
                exc_info=True,
                extra={"id": id},
            )
            raise BaseRespositoryException(DEFAULT_ERROR_DESCRIPTION) from e
        
    async def get_all(self) -> list[Entity]:
        if not self.model:
            raise BaseRespositoryException("The method cannot work without a model")
        query = Select(self.model)
        try:
            return (await self.session.execute(query)).scalars().all()
        except SQLAlchemyError as e:
            logger.critical(
                msg="Error getting data from method 'get_all'",
                exc_info=True,
            )
            raise BaseRespositoryException(DEFAULT_ERROR_DESCRIPTION) from e
        
    async def get_by_filters(self, **filters) -> list[Entity]:
        if not self.model:
            raise BaseRespositoryException("The method cannot work without a model")
        query = Select(self.model).where(*[getattr(self.model, k) == el for k, el in filters.items()])
        try:
            return (await self.session.execute(query)).scalars().all()
        except SQLAlchemyError as e:
            logger.critical(
                msg="Error getting data from method 'get_all'",
                exc_info=True,
                extra=filters
            )
            raise BaseRespositoryException(DEFAULT_ERROR_DESCRIPTION) from e
    
    async def delete_by_id(self, id: int):
        if not self.model:
            raise BaseRespositoryException("The method cannot work without a model")
        query = Delete(self.model).where(self.model.id==id).returning(self.model.id)
        try:
            return (await self.session.execute(query)).scalars().one_or_none()
        except SQLAlchemyError as e:
            logger.critical(
                msg="Error getting data from method 'get_all'",
                exc_info=True,
                extra={"id": id}
            )
            raise BaseRespositoryException(DEFAULT_ERROR_DESCRIPTION) from e
    
    async def delete_by_filters(self, want_del_all=False, **filters) -> list[int]:
        if not self.model:
            raise BaseRespositoryException("The method cannot work without a model")
        query = Delete(self.model)
        if not want_del_all and not filters:
            raise BaseRespositoryException("Change the parameter Want_del_all = True if you want to delete all records")
        if filters:
            query = query.where(*[getattr(self.model, k) == el for k, el in filters]).returning(self.model.id)
        try:
            return (await self.session.execute(query)).scalars().all()
        except SQLAlchemyError as e:
            logger.critical(
                msg="Error getting data from method 'get_all'",
                exc_info=True,
                extra=filters
            )
            raise BaseRespositoryException(DEFAULT_ERROR_DESCRIPTION) from e