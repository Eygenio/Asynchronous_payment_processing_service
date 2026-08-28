import asyncio
import logging
from uuid import UUID

from faststream import AckPolicy, FastStream
from faststream.rabbit.annotations import RabbitMessage

from src.application.services.payment_processing import PaymentProcessingService
from src.config.settings import settings
from src.core.enums import ProcessingState
from src.core.helpers import parse_retry_count, publish_to_dlq
from src.db.db import async_session_maker
from src.infrastructure.unit_of_work import SQLAlchemyUnitOfWork
from src.rabbit.broker import NEW_ROUTE, broker, create_rabbit, payments_exchange, payments_new_queue

logger = logging.getLogger(__name__)
app = FastStream(broker)


@broker.subscriber(payments_new_queue, payments_exchange, ack_policy=AckPolicy.MANUAL)
async def handle_payment_created(message: dict, msg: RabbitMessage) -> None:
    payment_id_raw = message.get("payment_id")
    if not payment_id_raw:
        try:
            await publish_to_dlq("missing_payment_id", message)
            await msg.ack()
        except Exception:
            logger.exception("Failed to route malformed message to DLQ")
            await msg.nack(requeue=True)
        return

    try:
        payment_id = UUID(payment_id_raw)
    except (ValueError, TypeError):
        try:
            await publish_to_dlq("invalid_payment_id", message, message_id=str(payment_id_raw))
            await msg.ack()
        except Exception:
            logger.exception("Failed to route malformed message to DLQ")
            await msg.nack(requeue=True)
        return

    retries = parse_retry_count(msg, NEW_ROUTE)
    if retries >= settings.outbox.max_consumer_retries:
        try:
            await publish_to_dlq(
                "consumer_retries_exhausted",
                {"payment_id": str(payment_id), "payload": message},
                message_id=str(payment_id),
            )
            await msg.ack()
        except Exception:
            logger.exception("Failed to publish exhausted message to DLQ")
            await msg.nack(requeue=True)
        return

    try:
        async with async_session_maker() as session:
            uow = SQLAlchemyUnitOfWork(session)
            state, _ = await PaymentProcessingService(uow).process_payment_created(payment_id)

        if state == ProcessingState.NOT_FOUND:
            logger.warning("Payment not found for message: %s", payment_id)
        elif state == ProcessingState.ALREADY_PROCESSED:
            logger.info("Payment already processed: %s", payment_id)

        await msg.ack()
    except Exception:
        logger.exception("Temporary processing error for payment %s", payment_id)
        await msg.nack(requeue=False)


@app.after_startup
async def startup_declarations() -> None:
    await create_rabbit()


if __name__ == "__main__":
    asyncio.run(app.run())
