import pytest

from src.application.services.payments import PaymentService
from src.core.enums import PaymentStatus

pytestmark = pytest.mark.unit


async def test_create_payment_new(payment_service: PaymentService, uow, payment_create_dto) -> None:
    data = payment_create_dto

    result = await payment_service.create_payment(data, data.description or "key")

    assert result.status is PaymentStatus.PENDING
    assert result.amount == data.amount
    assert result.currency is data.currency
    assert len(uow.outbox.items) == 1
    assert uow.commit_count == 1


async def test_create_payment_returns_existing_payment(payment_service: PaymentService, uow, payment_create_dto) -> None:
    data = payment_create_dto
    existing = await payment_service.create_payment(data, "idempotency-key")
    uow.commit_count = 0

    result = await payment_service.create_payment(data, "idempotency-key")

    assert result is existing
    assert uow.commit_count == 0
    assert len(uow.outbox.items) == 1


async def test_create_payment_rejects_different_payload(
    payment_service: PaymentService,
    payment_create_dto,
    different_payment_create_dto,
) -> None:
    first = payment_create_dto
    await payment_service.create_payment(first, "idempotency-key")
    second = different_payment_create_dto

    with pytest.raises(ValueError, match="different parameters"):
        await payment_service.create_payment(second, "idempotency-key")
