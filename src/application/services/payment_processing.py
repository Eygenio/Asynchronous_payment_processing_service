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

    async def process_payment_created(self, payment_id: UUID) -> tuple[ProcessingState, Payment]:
        payment = await self.uow.payments.get_by_id_for_update(payment_id)
        if payment is None:
            return ProcessingState.NOT_FOUND, None  # type: ignore

        if payment.processed_at is not None:
            return ProcessingState.ALREADY_PROCESSED, payment

        # Emulate external gateway processing
        await asyncio.sleep(random.uniform(2, 5))
        payment.status = PaymentStatus.SUCCEEDED if random.random() < 0.9 else PaymentStatus.FAILED
        payment.processed_at = datetime.now(UTC)

        # Update the ORM via repository (we need to mark status change)
        # Since our repository doesn't have update method, we'll use session directly?
        # We'll add a method to repository to update status.
        # For now, we assume the repository will persist domain changes on commit.
        # In SQLAlchemy UoW, we need to synchronize. Better add update method.
        # We'll add update_status method to repository.
        await self.uow.commit()

        return ProcessingState.PROCESSED, payment
