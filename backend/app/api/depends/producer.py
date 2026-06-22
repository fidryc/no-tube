from typing import Annotated

from fastapi import Depends, Request

from app.infrastructure.messages_broker.implementations.rabbitmq.producer import Producer

def get_producer(request: Request) -> Producer:
    return request.app.state.producer

ProducerDep = Annotated[Producer, Depends(get_producer)]