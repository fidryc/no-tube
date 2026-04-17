import json
from typing import Self

from app.infrastructure.messages_broker.interface import IProducer
import aio_pika
from app.core.logger import logger

class ProducerException(Exception):
    pass


NAME_EXCHANGE = "no-tube"
class Producer(IProducer):
    def __init__(self, url: str):
        self.url = url
        self.name_exchange = NAME_EXCHANGE
        self._connection = None
     
    async def __aenter__(self) -> Self:
        logger.debug("Enter rbmq producer")
        self._connection = await aio_pika.connect_robust(self.url)
        return self
           
    async def __aexit__(self, exc_type, exc, tb):
        logger.debug("Exit rbmq producer")
        if self._connection is not None:
            await self._connection.close()
    
    async def publish(self, queue_name: str, message: dict):
        if self._connection is None:
            raise ProducerException("Connection not created")
        
        async with self._connection.channel() as channel:
            exchange = await channel.declare_exchange(
                self.name_exchange, 
                aio_pika.ExchangeType.DIRECT
            )
            dlx_exchanger = await channel.declare_exchange(name="dlx_exchange", type=aio_pika.ExchangeType.DIRECT)
            dlx_queue = await channel.declare_queue(name="dlx_queue")
            await dlx_queue.bind(dlx_exchanger, "failed")
            msg = aio_pika.Message(json.dumps(message).encode("utf-8"))
            queue = await channel.declare_queue(
                queue_name,
                auto_delete=False,
                durable=True,
                arguments={
                    "x-dead-letter-exchange": "dlx_exchange",
                    "x-dead-letter-routing-key": "failed",
                    "x-queue-type": "quorum",
                    "x-delivery-limit": 5,
                }    
            )

            # Binding queue
            await queue.bind(exchange, queue_name)
            await exchange.publish(
                message=msg,
                routing_key=queue_name
            )