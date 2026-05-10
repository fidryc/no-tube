import uuid
from typing import Any, Protocol, TypeAlias, TypeVar, Generic

from sqlalchemy import ColumnElement

from app.repositories.filter.filter import And, Filter, Not, Or
from sqlalchemy.orm import DeclarativeBase


Model = TypeVar("Model", bound=DeclarativeBase)
Entity = TypeVar("Entity")

IdType: TypeAlias = int | uuid.UUID
CompositeId: TypeAlias = list[IdType]

ReturnedId: TypeAlias = IdType | tuple[Any, ...]
IdTitleColType: TypeAlias = str | list[str] | None


class IRepository(Protocol, Generic[Model, Entity]):
    model: type[Model] | None
    entity: type[Entity]

    async def get_by_id(
        self,
        id: IdType | CompositeId,
        id_title_col: IdTitleColType = "id"
    ) -> Entity | None:
        ...

    async def get_all(
        self,
        order_by_col_title: str | None = None,
        desc: bool | None = None,
        limit: int | None = None,
        offset: int | None = None
    ) -> list[Entity]:
        ...

    def to_expression(
        self,
        filter: And | Or | Not | Filter
    ) -> ColumnElement[bool]:
        ...

    async def get_by_filters(
        self,
        *filters: And | Or | Not | Filter,
        order_by_col_title: str | None = None,
        desc: bool | None = None,
        limit: int | None = None,
        offset: int | None = None
    ) -> list[Entity]:
        ...

    async def delete_by_id(
        self,
        id: IdType | CompositeId,
        id_title_col: IdTitleColType = "id"
    ) -> ReturnedId | None:
        ...

    async def delete_by_filters(
        self,
        filters: list[And | Or | Not | Filter],
        want_del_all: bool = False,
        id_title_col: IdTitleColType = "id"
    ) -> list[ReturnedId]:
        ...

    async def add(
        self,
        obj: dict,
        id_title_col: IdTitleColType = "id"
    ) -> ReturnedId | None:
        ...

    async def add_many(
        self,
        objs: list[dict],
        id_title_col: IdTitleColType = "id"
    ) -> list[ReturnedId]:
        ...

    async def update_many(
        self,
        filter: And | Or | Not | Filter,
        values: dict,
        id_title_col: IdTitleColType = "id"
    ) -> list[ReturnedId]:
        ...