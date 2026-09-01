import logging
from uuid import UUID

from sqlalchemy.exc import IntegrityError

from src.application.dto.payments import PaymentCreateDTO
from src.core.enums import OutboxStatus, PaymentStatus
from src.domain.entities import Outbox, Payment
from src.domain.unit_of_work import IUnitOfWork

logger = logging.getLogger(__name__)


class PaymentService:
    def __init__(self, uow: IUnitOfWork) -> None:
        self.uow = uow

    async def get_payment(self, payment_id: UUID) -> Payment | None:
        return await self.uow.payments.get_by_id(payment_id)

    async def create_payment(
        self,
        data: PaymentCreateDTO,
        idempotency_key: str,
    ) -> Payment:
        existing = await self.uow.payments.get_by_idempotency_key(idempotency_key)
        if existing:
            if not self._check_payload(existing, data):
                raise ValueError("Idempotency key already exists with different parameters.")
            return existing

        payment = Payment(
            amount=data.amount,
            currency=data.currency,
            description=data.description,
            metadata_=dict(data.metadata),
            status=PaymentStatus.PENDING,
            idempotency_key=idempotency_key,
            webhook_url=data.webhook_url,
        )
        await self.uow.payments.add(payment)

        outbox = Outbox(
            event_type="payments.new",
            payload={
                "payment_id": str(payment.payment_id),
                "idempotency_key": idempotency_key,
            },
            status=OutboxStatus.PENDING,
        )
        await self.uow.outbox.add(outbox)

        try:
            await self.uow.commit()
            await self.uow.payments.refresh(payment)
        except IntegrityError as error:
            await self.uow.rollback()
            existing = await self.uow.payments.get_by_idempotency_key(idempotency_key)
            if existing is None:
                raise
            if not self._check_payload(existing, data):
                raise ValueError(
                    "Idempotency key already exists with different parameters."
                ) from error
            return existing

        return payment

    @staticmethod
    def _check_payload(existing: Payment, data: PaymentCreateDTO) -> bool:
        return (
            existing.amount == data.amount
            and existing.currency == data.currency
            and existing.description == data.description
            and existing.metadata_ == data.metadata
            and existing.webhook_url == data.webhook_url
        )
