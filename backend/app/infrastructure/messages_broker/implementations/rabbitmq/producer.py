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
        self._exchange = None

    async def __aenter__(self) -> Self:
        logger.debug("Enter rbmq producer")
        self._connection = await aio_pika.connect_robust(self.url)

        channel = await self._connection.channel()

        self._exchange = await channel.declare_exchange(
            self.name_exchange,
            aio_pika.ExchangeType.DIRECT,
            durable=True
        )

        self._dlx_exchange = await channel.declare_exchange(
            "dlx_exchange",
            aio_pika.ExchangeType.DIRECT,
            durable=True
        )

        dlx_queue = await channel.declare_queue(name="dlx_queue", durable=True)
        await dlx_queue.bind(self._dlx_exchange, "failed")
        self._channel = channel

        return self

    async def __aexit__(self, exc_type, exc, tb):
        logger.debug("Exit rbmq producer")

        if self._channel:
            await self._channel.close()

        if self._connection:
            await self._connection.close()

    async def init_queue(self, queue_name: str):
        queue = await self._channel.declare_queue(
            queue_name,
            durable=True,
            arguments={
                "x-dead-letter-exchange": "dlx_exchange",
                "x-dead-letter-routing-key": "failed",
                "x-queue-type": "quorum",
                "x-delivery-limit": 5,
            }
        )

        await queue.bind(self._exchange, queue_name)

    async def publish(self, queue_name: str, message: dict):
        if self._exchange is None:
            raise ProducerException("Producer not initialized")

        msg = aio_pika.Message(
            body=json.dumps(message).encode()
        )

        await self._exchange.publish(
            msg,
            routing_key=queue_name
        )