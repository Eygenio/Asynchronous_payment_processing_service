from src.application.dto.payments import PaymentCreateDTO
from src.application.services.payments import PaymentService
from src.core.enums import Currency, PaymentStatus

from tests.factories import DEFAULT_CREATED_AT, DEFAULT_PAYMENT_ID, payment


async def test_create_payment_new(service: PaymentService, mock_uow) -> None:
    data = PaymentCreateDTO(
        amount=payment().amount,
        currency=payment().currency,
        description=payment().description,
        metadata={},
        webhook_url=None,
    )
    mock_uow.payments.get_by_idempotency_key.return_value = None

    result = await service.create_payment(data, "key-1")

    assert result.status is PaymentStatus.PENDING
    mock_uow.payments.add.assert_awaited_once()
    mock_uow.outbox.add.assert_awaited_once()
    mock_uow.commit.assert_awaited_once()


async def test_create_payment_returns_existing_payment(service: PaymentService, mock_uow) -> None:
    existing_payment = payment(
        payment_id=DEFAULT_PAYMENT_ID,
        idempotency_key="key-1",
        created_at=DEFAULT_CREATED_AT,
    )
    mock_uow.payments.get_by_idempotency_key.return_value = existing_payment

    data = PaymentCreateDTO(
        amount=existing_payment.amount,
        currency=existing_payment.currency,
        description=existing_payment.description,
        metadata=dict(existing_payment.metadata_),
        webhook_url=existing_payment.webhook_url,
    )

    result = await service.create_payment(data, "key-1")

    assert result is existing_payment
    mock_uow.commit.assert_not_awaited()
    mock_uow.outbox.add.assert_not_awaited()
