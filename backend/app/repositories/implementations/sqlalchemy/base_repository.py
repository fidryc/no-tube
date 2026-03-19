from sqlalchemy import ColumnElement, Delete, Insert, Select, Update, and_, not_, or_
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import DeclarativeBase
from app.repositories.exceptions import BaseRepositoryException
from app.repositories.filter.enum import Operation
from app.repositories.implementations.sqlalchemy.utils.converters import to_dict
from app.repositories.interfaces.base_repository import IRepository
from sqlalchemy.ext.asyncio import AsyncSession
from typing import TypeVar
from app.core.logger import logger
from app.utils.mapper import mapping_to_obj
from app.repositories.filter.filter import And, Logic, Filter, LogicTypes, Not, Or


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
            raise BaseRepositoryException(DEFAULT_ERROR_LACK_MODEL)
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
            raise BaseRepositoryException(DEFAULT_ERROR_DESCRIPTION) from e
        
    async def get_all(
        self,
        order_by_col_title: str | None = None,
        desc: bool | None = None,
        limit: int | None = None,
        offset: int | None = None
    ) -> list[Entity]:
        if not self.model:
            raise BaseRepositoryException(DEFAULT_ERROR_LACK_MODEL)
        query = Select(self.model)
        if order_by_col_title is not None:
            col = getattr(self.model, order_by_col_title)
            if desc is True:
                col = col.desc()
            query = query.order_by(col)
        if limit is not None:
            query = query.limit(limit)
        if offset is not None:
            query = query.offset(offset)
        try:
            models = (await self.session.execute(query)).scalars().all()
            return self.__convert_models_to_ent(models=models)
        except SQLAlchemyError as e:
            logger.critical(
                msg="Error getting data from method 'get_all'",
                exc_info=True,
            )
            raise BaseRepositoryException(DEFAULT_ERROR_DESCRIPTION) from e
        
    def __convert_models_to_ent(self, models: list[DeclarativeBase]) -> list:
        entities = [0] * len(models)
        for i, model in enumerate(models):
            # convert all find models to entities
            entities[i] = mapping_to_obj(to_dict(model), self.entity)
        return entities
         
    condition_func = {
        Operation.EQ: lambda obj, value: obj == value,
        Operation.NE: lambda obj, value: obj != value,
        Operation.LT: lambda obj, value: obj < value,
        Operation.LE: lambda obj, value: obj <= value,
        Operation.GT: lambda obj, value: obj > value,
        Operation.GE: lambda obj, value: obj >= value,
        Operation.IN: lambda obj, values: obj.in_(values),
        Operation.NOT_IN: lambda obj, values: obj.not_in(values)
    }

    logic_methods = {
        LogicTypes.AND: and_,
        LogicTypes.OR: or_,
        LogicTypes.NOT: not_
    }
    
    def to_expression(self, filter: And | Or | Not | Filter) -> ColumnElement:
        if isinstance(filter, Filter):
            if not hasattr(self.model, filter.col_title):
                raise AttributeError(f"Model {self.model} has no column '{filter.col_title}'")
            return self.condition_func[filter.operation](getattr(self.model, filter.col_title), filter.value)
        elif isinstance(filter, Logic):
            if not filter.conditions:
                raise ValueError("Logic filter must have at least one condition")
            return self.logic_methods[filter.type](*[self.to_expression(fil) for fil in filter.conditions])
            
                
    async def get_by_filters(
        self,
        *filters: And | Or | Not | Filter,
        order_by_col_title: str | None = None,
        desc: bool | None = None,
        limit: int | None = None,
        offset: int | None = None
    ) -> list[Entity]:
        if not self.model:
            raise BaseRepositoryException(DEFAULT_ERROR_LACK_MODEL)
        query = Select(self.model).where(*[self.to_expression(fil) for fil in filters])
        if order_by_col_title is not None:
            col = getattr(self.model, order_by_col_title)
            if desc is True:
                col = col.desc()
            query = query.order_by(col)
        if limit is not None:
            query = query.limit(limit)
        if offset is not None:
            query = query.offset(offset)
        try:
            models = (await self.session.execute(query)).scalars().all()
            return self.__convert_models_to_ent(models=models)
        except SQLAlchemyError as e:
            logger.critical(
                msg="Error getting data from method 'get_by_filters'",
                exc_info=True,
                extra=filters
            )
            raise BaseRepositoryException(DEFAULT_ERROR_DESCRIPTION) from e
    
    async def delete_by_id(self, id: int, id_title_col="id") -> int | None:
        if not self.model:
            raise BaseRepositoryException(DEFAULT_ERROR_LACK_MODEL)
        query = Delete(self.model).where(getattr(self.model, id_title_col)==id).returning(getattr(self.model, id_title_col))
        try:
            return (await self.session.execute(query)).scalars().one_or_none()
        except SQLAlchemyError as e:
            logger.critical(
                msg="Error 'delete_by_id'",
                exc_info=True,
                extra={"id": id}
            )
            raise BaseRepositoryException(DEFAULT_ERROR_DESCRIPTION) from e
    
    async def delete_by_filters(self, filters: list[And | Or | Not | Filter], want_del_all=False, id_title_col="id") -> list[int]:
        if not self.model:
            raise BaseRepositoryException(DEFAULT_ERROR_LACK_MODEL)
        query = Delete(self.model)
        if not want_del_all and not filters:
            raise BaseRepositoryException("Change the parameter Want_del_all = True if you want to delete all records")
        if filters:
            query = query.where(*[self.to_expression(fil) for fil in filters]).returning(getattr(self.model, id_title_col))
        try:
            return (await self.session.execute(query)).scalars().all()
        except SQLAlchemyError as e:
            logger.critical(
                msg="Error 'delete_by_filters'",
                exc_info=True,
                extra=filters
            )
            raise BaseRepositoryException(DEFAULT_ERROR_DESCRIPTION) from e
        
    async def add(self, obj: dict, id_title_col="id") -> int:
        if not self.model:
            raise BaseRepositoryException(DEFAULT_ERROR_LACK_MODEL)
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
            raise BaseRepositoryException(DEFAULT_ERROR_DESCRIPTION) from e
        
    async def add_many(self, objs: list[dict], id_title_col="id") -> list[int]:
        if not self.model:
            raise BaseRepositoryException(DEFAULT_ERROR_LACK_MODEL)
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
            raise BaseRepositoryException(DEFAULT_ERROR_DESCRIPTION) from e
        
    async def update(self, filter: And | Or | Not | Filter, values: dict, id_title_col="id") -> int:
        if not self.model:
            raise BaseRepositoryException(DEFAULT_ERROR_LACK_MODEL)
        query = Update(self.model).where(self.to_expression(filter)).values(**values).returning(getattr(self.model, id_title_col))
        
        try:
            print(query)
            id = (await self.session.execute(query)).scalars().one_or_none()
            return id
        except SQLAlchemyError as e:
            logger.critical(
                msg="Error 'update'",
                exc_info=True,
                extra={"filter": filter, "obj": values},
            )
            raise BaseRepositoryException(DEFAULT_ERROR_DESCRIPTION) from e
