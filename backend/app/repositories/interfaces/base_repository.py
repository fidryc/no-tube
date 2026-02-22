from typing import Protocol, TypeVar, Generic

Model = TypeVar("Model")
Entity = TypeVar("Entity")

class IRepository(Protocol, Generic[Model, Entity]):
    model: Model = None
    
    async def get_by_id(self, id: int) -> Entity | None:
        pass
    
    async def get_all(self) -> list[Entity]:
        pass
    
    async def get_by_filters(self, **filters) -> list[Entity]:
        pass
    
    async def delete_by_id(self, id: int):
        pass
    
    async def delete_by_filters(self, **filters):
        pass