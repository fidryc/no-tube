from sqlalchemy import Delete, Insert, Select, and_, or_
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import DeclarativeBase
from app.repositories.exceptions import BaseRespositoryException
from app.repositories.filter.impl.sqlalchemy.filter import Agregator, And, Or
from app.repositories.implementations.sqlalchemy.utils.converters import to_dict
from app.repositories.interfaces.base_repository import IRepository
from sqlalchemy.ext.asyncio import AsyncSession
from typing import TypeVar
from app.core.logger import logger
from app.utils.mapper import mapping_to_obj
from app.repositories.filter.enum import Operation
from app.repositories.filter.impl.sqlalchemy.filter import Filter


DEFAULT_ERROR_DESCRIPTION = "Unknow error in db"
DEFAULT_ERROR_LACK_MODEL = "The method cannot work without a model"

Model = TypeVar("Model", bound=DeclarativeBase)
Entity = TypeVar("Entity")

class Repository(IRepository[Model, Entity]):
    model: Model = None
    entity: Entity
    
    def __init__(self, session: AsyncSession):
        self.session = session
        
    async def get_by_id(self, id: int, id_title_col="id") -> Entity | None:
        if not self.model:
            raise BaseRespositoryException(DEFAULT_ERROR_LACK_MODEL)
        query = Select(self.model).where(getattr(self.model, id_title_col) == id)
        
        try:
            obj = (await self.session.execute(query)).scalars().one_or_none()
            try:
                ent = mapping_to_obj(to_dict(obj), self.entity)
                return ent
            except Exception as e:
                logger.critical(
                    "Failed to convert to entity",
                    exc_info=True,
                    extra={"obj": obj.__dict__ if obj else None}
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
            raise BaseRespositoryException(DEFAULT_ERROR_LACK_MODEL)
        query = Select(self.model)
        try:
            models = (await self.session.execute(query)).scalars().all()
            return self.__convert_models_to_ent(models=models)
        except SQLAlchemyError as e:
            logger.critical(
                msg="Error getting data from method 'get_all'",
                exc_info=True,
            )
            raise BaseRespositoryException(DEFAULT_ERROR_DESCRIPTION) from e
        
    def __convert_models_to_ent(self, models: list[DeclarativeBase]):
        entities = [0] * len(models)
        for i, model in enumerate(models):
            # convert all find models to entities
            entities[i] = mapping_to_obj(to_dict(model), self.entity)
        return entities
        
    def __parse(self, agregator: Agregator):
        if isinstance(agregator, Filter):
            return agregator.filter_value(self.model)
        args = []
        for condition in agregator.conditions:
            args.append(self.__parse(condition))
            
        if isinstance(agregator, Or):
            return or_(*args)
        elif isinstance(agregator, And):
            return and_(*args)
         
                
    async def get_by_filters(self, *filters: Filter | And | Or) -> list[Entity]:
        if not self.model:
            raise BaseRespositoryException(DEFAULT_ERROR_LACK_MODEL)
        query = Select(self.model).where(*[self.__parse(fil) for fil in filters])
        try:
            models = (await self.session.execute(query)).scalars().all()
            return self.__convert_models_to_ent(models=models)
        except SQLAlchemyError as e:
            logger.critical(
                msg="Error getting data from method 'get_by_filters'",
                exc_info=True,
                extra=filters
            )
            raise BaseRespositoryException(DEFAULT_ERROR_DESCRIPTION) from e
    
    async def delete_by_id(self, id: int, id_title_col="id") -> int | None:
        if not self.model:
            raise BaseRespositoryException(DEFAULT_ERROR_LACK_MODEL)
        query = Delete(self.model).where(getattr(self.model, id_title_col)==id).returning(getattr(self.model, id_title_col))
        try:
            return (await self.session.execute(query)).scalars().one_or_none()
        except SQLAlchemyError as e:
            logger.critical(
                msg="Error 'delete_by_id'",
                exc_info=True,
                extra={"id": id}
            )
            raise BaseRespositoryException(DEFAULT_ERROR_DESCRIPTION) from e
    
    async def delete_by_filters(self, want_del_all=False, id_title_col="id", **filters) -> list[int]:
        if not self.model:
            raise BaseRespositoryException(DEFAULT_ERROR_LACK_MODEL)
        query = Delete(self.model)
        if not want_del_all and not filters:
            raise BaseRespositoryException("Change the parameter Want_del_all = True if you want to delete all records")
        if filters:
            query = query.where(*[getattr(self.model, k) == el for k, el in filters.items()]).returning(getattr(self.model, id_title_col))
        try:
            return (await self.session.execute(query)).scalars().all()
        except SQLAlchemyError as e:
            logger.critical(
                msg="Error 'delete_by_filters'",
                exc_info=True,
                extra=filters
            )
            raise BaseRespositoryException(DEFAULT_ERROR_DESCRIPTION) from e
        
    async def add(self, obj: dict, id_title_col="id") -> int:
        if not self.model:
            raise BaseRespositoryException(DEFAULT_ERROR_LACK_MODEL)
        query = Insert(self.model).values(**obj).returning(getattr(self.model, id_title_col))
        
        try:
            id = (await self.session.execute(query)).scalars().one_or_none()
            return id
        except SQLAlchemyError as e:
            logger.critical(
                msg="Error 'add'",
                exc_info=True,
                extra={"obj": obj},
            )
            raise BaseRespositoryException(DEFAULT_ERROR_DESCRIPTION) from e
        
    async def add_many(self, objs: list[dict], id_title_col="id") -> list[int]:
        if not self.model:
            raise BaseRespositoryException(DEFAULT_ERROR_LACK_MODEL)
        query = Insert(self.model).values(objs).returning(getattr(self.model, id_title_col))
        
        try:
            ids = (await self.session.execute(query)).scalars().all()
            return ids
        except SQLAlchemyError as e:
            logger.critical(
                msg="Error 'add'",
                exc_info=True,
                extra={"obj": objs},
            )
            raise BaseRespositoryException(DEFAULT_ERROR_DESCRIPTION) from e