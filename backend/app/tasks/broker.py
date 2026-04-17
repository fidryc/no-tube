from taskiq_aio_pika import AioPikaBroker

broker = AioPikaBroker(
    url="amqp://guest:guest@localhost:5672" # TODO: вынести в конфиг
)
