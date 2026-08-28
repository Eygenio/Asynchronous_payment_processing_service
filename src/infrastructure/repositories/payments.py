from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities import Payment
from src.domain.repositories import IPaymentRepository
from src.infrastructure.models.payments import PaymentOrm


class PaymentRepository(IPaymentRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @staticmethod
    def _to_domain(orm: PaymentOrm) -> Payment:
        return Payment(
            payment_id=orm.payment_id,
            amount=orm.amount,
            currency=orm.currency,
            description=orm.description,
            metadata_=orm.metadata_,
            status=orm.status,
            idempotency_key=orm.idempotency_key,
            webhook_url=orm.webhook_url,
            created_at=orm.created_at,
            processed_at=orm.processed_at,
        )

    async def get_by_id(self, payment_id: UUID) -> Payment | None:
        result = await self._session.get(PaymentOrm, payment_id)
        return self._to_domain(result) if result else None

    async def get_by_id_for_update(self, payment_id: UUID) -> Payment | None:
        statement = select(PaymentOrm).where(PaymentOrm.payment_id == payment_id).with_for_update()
        result = await self._session.execute(statement)
        orm = result.scalar_one_or_none()
        return self._to_domain(orm) if orm else None

    async def get_by_idempotency_key(self, idempotency_key: str) -> Payment | None:
        statement = select(PaymentOrm).where(PaymentOrm.idempotency_key == idempotency_key)
        result = await self._session.execute(statement)
        orm = result.scalar_one_or_none()
        return self._to_domain(orm) if orm else None

    async def add(self, payment: Payment) -> Payment:
        orm = PaymentOrm(
            amount=payment.amount,
            currency=payment.currency,
            description=payment.description,
            metadata_=payment.metadata_,
            status=payment.status,
            idempotency_key=payment.idempotency_key,
            webhook_url=payment.webhook_url,
        )
        self._session.add(orm)
        await self._session.flush()
        payment.payment_id = orm.payment_id
        payment.created_at = orm.created_at
        return payment

    async def refresh(self, payment: Payment) -> None:
        if payment.payment_id is None:
            raise ValueError("payment_id is None")
        orm = await self._session.get(PaymentOrm, payment.payment_id)
        if orm:
            refreshed = self._to_domain(orm)
            payment.payment_id = refreshed.payment_id
            payment.created_at = refreshed.created_at
            payment.status = refreshed.status

    async def update_status(self, payment: Payment) -> None:
        if payment.payment_id is None:
            raise ValueError("payment_id is None")
        orm = await self._session.get(PaymentOrm, payment.payment_id)
        if orm:
            orm.status = payment.status
            orm.processed_at = payment.processed_at
