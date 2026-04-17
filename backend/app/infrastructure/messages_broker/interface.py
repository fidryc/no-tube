from typing import Protocol

class IProducer(Protocol):
    async def publish(self, queue: str, message: dict): pass