import logging

from src.core.exponential_retries import attempts_exhausted, backoff_delay
from src.domain.unit_of_work import IUnitOfWork
from src.rabbit.producer import publish_payment_new, publish_payment_to_dlq

logger = logging.getLogger(__name__)


class OutboxService:
    def __init__(self, uow: IUnitOfWork) -> None:
        self.uow = uow

    async def dispatch_pending_outbox(self, limit: int = 100) -> dict:
        sent_count = 0
        failed_count = 0

        messages = await self.uow.outbox.get_ready_for_dispatch(limit=limit)

        for message in messages:
            try:
                await publish_payment_new(message.payload, message_id=str(message.id))
                await self.uow.outbox.mark_published(message)
                sent_count += 1
                await self.uow.commit()
            except Exception:
                logger.exception("Outbox message publish failed: %s", message.id)
                attempts = message.retry_count + 1

                if attempts_exhausted(attempts=attempts):
                    await self.uow.outbox.mark_failed(message, attempts=attempts)
                    failed_count += 1
                    try:
                        await publish_payment_to_dlq(
                            message.payload,
                            message_id=str(message.id),
                        )
                    except Exception:
                        logger.exception(
                            "Failed to publish to DLQ for outbox message %s",
                            message.id,
                        )
                else:
                    await self.uow.outbox.schedule_retry(
                        message,
                        attempts=attempts,
                        next_retry_at=backoff_delay(attempts),
                    )
                await self.uow.commit()

        return {
            "selected": len(messages),
            "sent": sent_count,
            "failed": failed_count,
        }
