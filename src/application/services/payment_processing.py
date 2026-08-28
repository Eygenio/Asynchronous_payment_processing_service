import asyncio
import random
from datetime import UTC, datetime
from uuid import UUID

from src.domain.entities import Payment
from src.domain.unit_of_work import IUnitOfWork
from src.core.enums import PaymentStatus, ProcessingState


class PaymentProcessingService:
    def __init__(self, uow: IUnitOfWork) -> None:
        self.uow = uow

    async def process_payment_created(
        self,
        payment_id: UUID,
    ) -> tuple[ProcessingState, Payment | None]:
        payment = await self.uow.payments.get_by_id_for_update(payment_id)
        if payment is None:
            return ProcessingState.NOT_FOUND, None

        if payment.processed_at is not None:
            return ProcessingState.ALREADY_PROCESSED, payment

        await asyncio.sleep(random.uniform(2, 5))
        payment.status = PaymentStatus.SUCCEEDED if random.random() < 0.9 else PaymentStatus.FAILED
        payment.processed_at = datetime.now(UTC)

        await self.uow.payments.update_status(payment)
        await self.uow.commit()

        return ProcessingState.PROCESSED, payment
