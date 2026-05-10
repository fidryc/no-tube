import uuid

from sqlalchemy import delete, insert, select, update
from sqlalchemy import ColumnElement, and_, not_, or_
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import DeclarativeBase
from app.repositories.exceptions import BaseRepositoryException
from app.repositories.filter.enum import Operation
from app.repositories.implementations.sqlalchemy.utils.converters import to_dict
from app.repositories.interfaces.base_repository import IRepository
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any, Optional, TypeAlias, TypeVar
from app.core.logger import logger
from app.utils.mapper import mapping_to_obj
from app.repositories.filter.filter import And, Logic, Filter, LogicTypes, Not, Or


DEFAULT_ERROR_DESCRIPTION = "Unknow error in db"
DEFAULT_ERROR_LACK_MODEL = "The method cannot work without a model"

Model = TypeVar("Model", bound=DeclarativeBase)
Entity = TypeVar("Entity")

IdType: TypeAlias = int | uuid.UUID
CompositeId: TypeAlias = list[IdType]
ReturnedId: TypeAlias = IdType | tuple[Any, ...]
IdTitleColType: TypeAlias = str | list[str] | None

class Repository(IRepository[Model, Entity]):
    model: Model = None
    entity: Entity

    def __init__(self, session: AsyncSession):
        self.session = session
        
    def _apply_returning(
        self,
        query,
        id_title_col: IdTitleColType
    ):
        if isinstance(id_title_col, str):
            return query.returning(getattr(self.model, id_title_col))

        elif isinstance(id_title_col, list):
            return query.returning(
                *[getattr(self.model, col) for col in id_title_col]
            )

        return query
    
    def _apply_filter_by_id(
        self,
        query,
        id: IdType | CompositeId,
        id_title_col: IdTitleColType
    ):
        if id_title_col is None:
            raise BaseRepositoryException(
                "id_title_col cannot be None in filter operations"
            )
        if isinstance(id_title_col, str):
            if isinstance(id, list):
                raise BaseRepositoryException(
                    "Single id column requires scalar id"
                )

        elif isinstance(id_title_col, list):
            if not isinstance(id, list):
                raise BaseRepositoryException(
                    "Composite id columns require composite id"
                )
        if isinstance(id_title_col, str):
            return query.where(getattr(self.model, id_title_col) == id)

        elif isinstance(id_title_col, list):
            if len(id) != len(id_title_col):
                raise BaseRepositoryException("len param 'id' != len id_title_col")
            return query.where(
                *[
                    getattr(self.model, col) == val
                    for col, val in zip(id_title_col, id)
                ]
            )
        return query

    def _extract_returning_result(
        self,
        result,
        id_title_col: IdTitleColType
    ):
        if isinstance(id_title_col, str):
            return result.scalars().one_or_none()

        elif isinstance(id_title_col, list):
            row = result.fetchone()
            return tuple(row) if row else None

        return None

    async def get_by_id(self, id: IdType | CompositeId, id_title_col: IdTitleColType = "id") -> Entity | None:
        if not self.model:
            raise BaseRepositoryException(DEFAULT_ERROR_LACK_MODEL)
        query = select(self.model)
        
        query = self._apply_filter_by_id(
            query=query,
            id=id,
            id_title_col=id_title_col,
        )
        
        try:
            obj = (await self.session.execute(query)).scalars().one_or_none()
            if obj is None:
                return None
            try:
                ent = mapping_to_obj(to_dict(obj), self.entity)
                return ent
            except Exception as e:
                logger.critical(
                    f"{self.__class__.__name__}: Failed to convert to entity",
                    exc_info=True,
                    extra={"obj": obj.__dict__ if obj else None}
                )
                raise BaseRepositoryException("Failed to convert to entity") from e
        except SQLAlchemyError as e:
            logger.critical(
                msg=f"{self.__class__.__name__}: Error getting data from method 'get_by_id'",
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
        query = select(self.model)
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
                msg=f"{self.__class__.__name__}: Error getting data from method 'get_all'",
                exc_info=True,
            )
            raise BaseRepositoryException(DEFAULT_ERROR_DESCRIPTION) from e
        
    def __convert_models_to_ent(self, models: list[DeclarativeBase]) -> list[Entity]:
        entities = [0] * len(models)
        for i, model in enumerate(models):
            # convert all find models to entities
            try:
                entities[i] = mapping_to_obj(to_dict(model), self.entity)
            except Exception as e:
                logger.critical(
                    f"{self.__class__.__name__}: Failed to convert to entity",
                    exc_info=True,
                    extra={"obj": model.__dict__ if model else None}
                )
                raise BaseRepositoryException("Failed to convert to entity") from e
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
        raise TypeError(f"Unsupported filter type: {type(filter)}")
        
                
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
        query = select(self.model).where(*[self.to_expression(fil) for fil in filters])
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
                msg=f"{self.__class__.__name__}: Error getting data from method 'get_by_filters'",
                exc_info=True,
                extra=filters
            )
            raise BaseRepositoryException(DEFAULT_ERROR_DESCRIPTION) from e
    
    async def delete_by_id(self, id: IdType | CompositeId, id_title_col: IdTitleColType = "id") -> ReturnedId | None:
        if not self.model:
            raise BaseRepositoryException(DEFAULT_ERROR_LACK_MODEL)
        query = delete(self.model)
        
        query = self._apply_filter_by_id(
            query=query,
            id=id,
            id_title_col=id_title_col
        )
        
        query = self._apply_returning(
            query=query,
            id_title_col=id_title_col
        )
            
        try:
            res = (await self.session.execute(query))
            res_returning = self._extract_returning_result(res, id_title_col=id_title_col)
            return res_returning
        except SQLAlchemyError as e:
            logger.critical(
                msg=f"{self.__class__.__name__}: Error 'delete_by_id'",
                exc_info=True,
                extra={"id": id}
            )
            raise BaseRepositoryException(DEFAULT_ERROR_DESCRIPTION) from e
    
    def _extract_many_returning_result(
        self,
        result,
        id_title_col: IdTitleColType
    ) -> list[ReturnedId]:
        if id_title_col is None:
            return []
        if isinstance(id_title_col, str):
            return result.scalars().all()

        elif isinstance(id_title_col, list):
            return [tuple(row) for row in result.fetchall()]

        return []
    
    async def delete_by_filters(
        self,
        filters: list[And | Or | Not | Filter],
        want_del_all=False,
        id_title_col: IdTitleColType="id"
    ) -> list[ReturnedId]:
        if not self.model:
            raise BaseRepositoryException(DEFAULT_ERROR_LACK_MODEL)
        query = delete(self.model)
        if not want_del_all and not filters:
            raise BaseRepositoryException("Change the parameter Want_del_all = True if you want to delete all records")
        
        query = self._apply_returning(query, id_title_col)
        if filters:
            query = query.where(*[self.to_expression(fil) for fil in filters])
        try:
            res = (await self.session.execute(query))
            res = self._extract_many_returning_result(res, id_title_col)
            return res
        except SQLAlchemyError as e:
            logger.critical(
                msg=f"{self.__class__.__name__}: Error 'delete_by_filters'",
                exc_info=True,
                extra=filters
            )
            raise BaseRepositoryException(DEFAULT_ERROR_DESCRIPTION) from e
        
    async def add(self, obj: dict, id_title_col: IdTitleColType ="id") -> ReturnedId | None:
        if not self.model:
            raise BaseRepositoryException(DEFAULT_ERROR_LACK_MODEL)
        query = insert(self.model).values(**obj)
        query = self._apply_returning(query, id_title_col)
        
        try:
            res = (await self.session.execute(query))
            res_returning = self._extract_returning_result(res, id_title_col)
            return res_returning
        except SQLAlchemyError as e:
            logger.critical(
                msg=f"{self.__class__.__name__}: Error 'add'",
                exc_info=True,
                extra={"obj": obj},
            )
            raise BaseRepositoryException(DEFAULT_ERROR_DESCRIPTION) from e
        
    async def add_many(self, objs: list[dict], id_title_col: IdTitleColType = "id") -> list[ReturnedId]:
        if not self.model:
            raise BaseRepositoryException(DEFAULT_ERROR_LACK_MODEL)
        query = insert(self.model).values(objs)
        
        query = self._apply_returning(query, id_title_col)
        
        try:
            res = (await self.session.execute(query))
            res_returning = self._extract_many_returning_result(res, id_title_col)
            return res_returning
        except SQLAlchemyError as e:
            logger.critical(
                msg=f"{self.__class__.__name__}: Error 'add_many'",
                exc_info=True,
                extra={"obj": objs},
            )
            raise BaseRepositoryException(DEFAULT_ERROR_DESCRIPTION) from e
        
    async def update_many(self, filter: And | Or | Not | Filter, values: dict, id_title_col: IdTitleColType="id") -> list[ReturnedId]:
        if not self.model:
            raise BaseRepositoryException(DEFAULT_ERROR_LACK_MODEL)
        query = update(self.model).where(self.to_expression(filter)).values(**values)
        query = self._apply_returning(query, id_title_col)
        
        try:
            res = (await self.session.execute(query))
            res_returning = self._extract_many_returning_result(res, id_title_col)
            return res_returning
        except SQLAlchemyError as e:
            logger.critical(
                msg=f"{self.__class__.__name__}: Error 'update'",
                exc_info=True,
                extra={"filter": filter, "obj": values},
            )
            raise BaseRepositoryException(DEFAULT_ERROR_DESCRIPTION) from e
