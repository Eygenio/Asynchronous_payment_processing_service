import asyncio
import logging
from datetime import UTC, datetime, timedelta

from src.application.services.webhooks import PaymentWebhookSender
from src.config.settings import settings
from src.core.exponential_retries import attempts_exhausted, backoff_delay
from src.db.db import async_session_maker
from src.infrastructure.unit_of_work import SQLAlchemyUnitOfWork
from src.core.constants import BATCH_SIZE, POLL_INTERVAL_SECONDS

logger = logging.getLogger(__name__)

LEASE_SECONDS = max(settings.webhook.timeout_seconds * 2, 30)


async def process_batch() -> int:
    async with async_session_maker() as session:
        uow = SQLAlchemyUnitOfWork(session)
        lease_until = datetime.now(UTC) + timedelta(seconds=LEASE_SECONDS)
        deliveries = await uow.webhooks.claim_ready(BATCH_SIZE, lease_until)
        await uow.commit()

    if not deliveries:
        return 0

    sender = PaymentWebhookSender(
        timeout_seconds=settings.webhook.timeout_seconds,
        max_attempts=settings.webhook.max_attempts,
        base_delay_seconds=settings.webhook.base_delay_seconds,
        allow_private_networks=settings.webhook.allow_private_networks,
    )

    processed = 0
    for delivery in deliveries:
        try:
            await sender.send(delivery.target_url, delivery.payload)
        except Exception as error:
            attempts = delivery.retry_count + 1
            async with async_session_maker() as session:
                update_uow = SQLAlchemyUnitOfWork(session)
                if attempts_exhausted(attempts, settings.webhook.max_attempts):
                    await update_uow.webhooks.mark_failed(delivery, attempts, str(error))
                else:
                    await update_uow.webhooks.schedule_retry(
                        delivery,
                        attempts,
                        backoff_delay(attempts, settings.webhook.base_delay_seconds),
                        str(error),
                    )
                await update_uow.commit()
            logger.warning(
                "Webhook delivery failed payment=%s attempt=%s error=%s",
                delivery.payment_id,
                attempts,
                error,
            )
        else:
            async with async_session_maker() as session:
                update_uow = SQLAlchemyUnitOfWork(session)
                await update_uow.webhooks.mark_delivered(delivery)
                await update_uow.commit()
            logger.info("Webhook delivered payment=%s", delivery.payment_id)
        processed += 1

    return processed


async def run_webhook_dispatcher() -> None:
    logger.info("Webhook dispatcher started")
    while True:
        try:
            processed = await process_batch()
            if processed:
                logger.info("Webhook dispatch processed=%s", processed)
            await asyncio.sleep(POLL_INTERVAL_SECONDS)
        except Exception:
            logger.exception("Webhook dispatcher iteration failed")
            await asyncio.sleep(3)


if __name__ == "__main__":
    asyncio.run(run_webhook_dispatcher())
