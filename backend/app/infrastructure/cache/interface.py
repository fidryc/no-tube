from typing import Any, Protocol, Self


class ICache(Protocol):
    def __init__(self):
        self._connection = None
        
    async def __aenter__(self) -> None: pass
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None: pass
    
    async def get(self, key: str) -> Any: pass
    
    async def set(self, key: str, value: Any, ex: int): pass

    async def dict_set(self, key: str, value: dict, ex: int | None = None): pass
    
    async def dict_get(self, key: str): pass
    
    async def dict_get_field(self, key: str, field: str): pass
    
    async def dict_delete(self, key: str): pass