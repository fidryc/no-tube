from typing import Protocol

class IProducer(Protocol):
    async def publish(self, queue: str, message: dict): pass
    
    async def init_queue(self, queue_name: str): pass