import pytest
from unittest.mock import MagicMock

from src.application.services.payments import PaymentService
from src.domain.entities import Payment
from src.domain.unit_of_work import IUnitOfWork
from src.presentation.schemas.payments import PaymentCreateRequest
from src.common.enums import Currency, PaymentStatus

pytestmark = pytest.mark.asyncio


@pytest.fixture
def service(mock_uow: IUnitOfWork) -> PaymentService:
    return PaymentService(mock_uow)

async def test_create_payment_new(service: PaymentService, mock_uow: MagicMock) -> None:
    data = PaymentCreateRequest(
        amount="100.00",
        currency=Currency.USD,
        description="test",
        metadata={},
        webhook_url=None,
    )
    idempotency_key = "key1"
    mock_uow.payments.get_by_idempotency_key.return_value = None

    async def add_side_effect(payment: Payment) -> Payment:
        payment.payment_id = UUID("12345678-1234-5678-1234-567812345678")
        payment.created_at = datetime(2025, 1, 1)
        return payment
    mock_uow.payments.add.side_effect = add_side_effect

    async def outbox_add_side_effect(outbox):
        outbox.id = UUID("87654321-4321-8765-4321-876543210987")
        outbox.created_at = datetime(2025, 1, 1)
        return outbox
    mock_uow.outbox.add.side_effect = outbox_add_side_effect

    result = await service.create_payment(data, idempotency_key)

    assert result.payment_id is not None
    assert result.status == PaymentStatus.PENDING
    mock_uow.payments.add.assert_called_once()
    mock_uow.outbox.add.assert_called_once()
    mock_uow.commit.assert_called_once()
