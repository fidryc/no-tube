from typing import Any, Protocol, TypeVar, Generic
import uuid

from app.repositories.filter.filter import And, Filter, Not, Or

Model = TypeVar("Model")
Entity = TypeVar("Entity")

class IRepository(Protocol, Generic[Model, Entity]):
    model: Model = None
    
    async def get_by_id(self, id: int) -> Entity | None:
        pass
    
    async def get_all(self) -> list[Entity]:
        pass
    
    def to_expression(self, filter: And | Or | Not | Filter) -> Any: 
        pass
        
    async def get_by_filters(self, *filters: And | Or | Not | Filter) -> list[Entity]:
        pass
    
    async def delete_by_id(self, id: int, id_title_col="id") -> int | None:
        pass
    
    async def delete_by_filters(self, filters: list[And | Or | Not | Filter], want_del_all=False, id_title_col="id") -> list[int]:
        pass
    
    async def add(self, obj: dict, id_title_col: str | list[str] | None ="id") -> int | uuid.UUID:
        pass
    
    async def add_many(self, objs: list[dict], id_title_col="id") -> list[int]:
        pass
    
    async def update(self, filter: And | Or | Not | Filter, values: dict, id_title_col="id") -> int:
        pass
    