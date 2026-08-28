from faststream.rabbit import RabbitBroker, RabbitExchange, RabbitQueue

from src.config.settings import settings

PAYMENTS_EXCH = settings.payment.exchange_name
PAYMENTS_DLX = settings.payment.dlx_name
NEW_ROUTE = settings.payment.new_route
RETRY_ROUTE = settings.payment.retry_route
DLQ_ROUTE = settings.payment.dlq_route
PAYMENTS_RETRY_DELAY_MS = settings.payment.retry_delay_ms

payments_exchange = RabbitExchange(PAYMENTS_EXCH, durable=True)
payments_dlx_exchange = RabbitExchange(PAYMENTS_DLX, durable=True)

payments_new_queue = RabbitQueue(
    name=NEW_ROUTE,
    durable=True,
    routing_key=NEW_ROUTE,
    arguments={
        "x-dead-letter-exchange": PAYMENTS_DLX,
        "x-dead-letter-routing-key": RETRY_ROUTE,
    },
)

payments_retry_queue = RabbitQueue(
    name=RETRY_ROUTE,
    durable=True,
    routing_key=RETRY_ROUTE,
    arguments={
        "x-message-ttl": PAYMENTS_RETRY_DELAY_MS,
        "x-dead-letter-exchange": PAYMENTS_EXCH,
        "x-dead-letter-routing-key": NEW_ROUTE,
    },
)

payments_new_dlq_queue = RabbitQueue(
    name=DLQ_ROUTE,
    durable=True,
    routing_key=DLQ_ROUTE,
)

broker = RabbitBroker(settings.broker.url)


async def create_rabbit() -> None:
    await broker.declare_exchange(payments_exchange)
    await broker.declare_exchange(payments_dlx_exchange)
    await broker.declare_queue(payments_new_queue)
    await broker.declare_queue(payments_retry_queue)
    await broker.declare_queue(payments_new_dlq_queue)
