import logging
from datetime import UTC, datetime, timedelta

from src.application.dto.outbox import OutboxDispatchResult
from src.config.settings import settings
from src.core.exponential_retries import attempts_exhausted, backoff_delay
from src.db.db import async_session_maker
from src.domain.unit_of_work import IUnitOfWork
from src.infrastructure.unit_of_work import SQLAlchemyUnitOfWork
from src.rabbit.producer import publish_payment_new, publish_payment_to_dlq

logger = logging.getLogger(__name__)


class OutboxService:
    def __init__(self, uow: IUnitOfWork) -> None:
        self.uow = uow

    async def dispatch_pending_outbox(
        self,
        limit: int = 100,
    ) -> OutboxDispatchResult:
        lease_until = datetime.now(UTC) + timedelta(seconds=settings.outbox.lease_seconds)
        messages = await self.uow.outbox.claim_ready_for_dispatch(
            limit=limit,
            lease_until=lease_until,
        )
        await self.uow.commit()

        if not messages:
            return OutboxDispatchResult(selected=0, sent=0, failed=0)

        sent_count = 0
        failed_count = 0

        for message in messages:
            try:
                await publish_payment_new(
                    message.payload,
                    message_id=str(message.id),
                )
            except Exception:
                logger.exception("Outbox message publish failed: %s", message.id)
                attempts = message.retry_count + 1

                async with async_session_maker() as session:
                    update_uow = SQLAlchemyUnitOfWork(session)
                    if attempts_exhausted(attempts=attempts):
                        try:
                            await publish_payment_to_dlq(
                                message.payload,
                                message_id=str(message.id),
                            )
                        except Exception:
                            logger.exception(
                                "Failed to publish DLQ for outbox message %s",
                                message.id,
                            )
                            await update_uow.outbox.schedule_retry(
                                message,
                                attempts=attempts,
                                next_retry_at=backoff_delay(attempts),
                            )
                        else:
                            await update_uow.outbox.mark_failed(message, attempts=attempts)
                            failed_count += 1
                    else:
                        await update_uow.outbox.schedule_retry(
                            message,
                            attempts=attempts,
                            next_retry_at=backoff_delay(attempts),
                        )
                    await update_uow.commit()
                continue

            async with async_session_maker() as session:
                update_uow = SQLAlchemyUnitOfWork(session)
                await update_uow.outbox.mark_published(message)
                await update_uow.commit()
            sent_count += 1

        return OutboxDispatchResult(
            selected=len(messages),
            sent=sent_count,
            failed=failed_count,
        )
