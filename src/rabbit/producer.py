from typing import Any
from src.rabbit.broker import (
    DLQ_ROUTE,
    NEW_ROUTE,
    broker,
    payments_dlx_exchange,
    payments_exchange,
)


async def publish_payment_new(
    message: dict[str, Any],
    message_id: str | None = None,
) -> None:
    await broker.publish(
        message=message,
        exchange=payments_exchange,
        routing_key=NEW_ROUTE,
        message_id=message_id,
        persist=True,
        mandatory=True,
    )

async def publish_payment_to_dlq(
    message: dict[str, Any],
    message_id: str | None = None,
) -> None:
    await broker.publish(
        message=message,
        exchange=payments_dlx_exchange,
        routing_key=DLQ_ROUTE,
        message_id=message_id,
        persist=True,
        mandatory=True,
    )
