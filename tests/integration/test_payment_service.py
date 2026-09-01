import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.dto.payments import PaymentCreateDTO
from src.application.services.payments import PaymentService
from src.core.enums import OutboxStatus
from src.infrastructure.models.outbox import OutboxOrm
from src.infrastructure.unit_of_work import SQLAlchemyUnitOfWork

pytestmark = pytest.mark.integration


async def test_payment_service_creates_payment_and_outbox_atomically(
    integration_uow: SQLAlchemyUnitOfWork,
    integration_session: AsyncSession,
    payment_create_dto: PaymentCreateDTO,
) -> None:
    service = PaymentService(integration_uow)
    data = payment_create_dto
    idempotency_key = "integration-create-key"

    result = await service.create_payment(data, idempotency_key)

    stored_payment = await integration_uow.payments.get_by_id(result.payment_id)
    outbox_result = await integration_session.execute(select(OutboxOrm))
    outbox = outbox_result.scalar_one()

    assert stored_payment is not None
    assert stored_payment.amount == data.amount
    assert stored_payment.currency is data.currency
    assert outbox.status is OutboxStatus.PENDING
    assert outbox.payload["payment_id"] == str(result.payment_id)


async def test_payment_service_returns_existing_payment(
    integration_uow: SQLAlchemyUnitOfWork,
    payment_create_dto: PaymentCreateDTO,
) -> None:
    service = PaymentService(integration_uow)
    data = payment_create_dto
    key = "integration-idempotency-key"

    first = await service.create_payment(data, key)
    second = await service.create_payment(data, key)

    assert second.payment_id == first.payment_id
    assert second.amount == first.amount
