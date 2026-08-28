import asyncio
import random
from datetime import UTC, datetime
from uuid import UUID

from src.core.enums import PaymentStatus, ProcessingState
from src.domain.entities import Payment, WebhookOutbox
from src.domain.unit_of_work import IUnitOfWork


class PaymentProcessingService:
    def __init__(self, uow: IUnitOfWork) -> None:
        self.uow = uow

    async def process_payment_created(
        self,
        payment_id: UUID,
    ) -> tuple[ProcessingState, Payment | None]:
        payment = await self.uow.payments.get_by_id(payment_id)
        if payment is None:
            await self.uow.rollback()
            return ProcessingState.NOT_FOUND, None

        if payment.processed_at is not None:
            await self.uow.rollback()
            return ProcessingState.ALREADY_PROCESSED, payment

        await self.uow.rollback()

        await asyncio.sleep(random.uniform(2, 5))
        new_status = (
            PaymentStatus.SUCCEEDED
            if random.random() < 0.9
            else PaymentStatus.FAILED
        )

        payment = await self.uow.payments.get_by_id_for_update(payment_id)
        if payment is None:
            await self.uow.rollback()
            return ProcessingState.NOT_FOUND, None

        if payment.processed_at is not None:
            await self.uow.rollback()
            return ProcessingState.ALREADY_PROCESSED, payment

        payment.status = new_status
        payment.processed_at = datetime.now(UTC)
        await self.uow.payments.update_status(payment)

        if payment.webhook_url and payment.payment_id is not None:
            await self.uow.webhooks.add(
                WebhookOutbox(
                    payment_id=payment.payment_id,
                    target_url=payment.webhook_url,
                    payload={
                        "payment_id": str(payment.payment_id),
                        "status": payment.status.value,
                        "processed_at": payment.processed_at.isoformat(),
                    },
                )
            )

        await self.uow.commit()
        return ProcessingState.PROCESSED, payment
