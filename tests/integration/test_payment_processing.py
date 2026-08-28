from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

import pytest

from src.application.services.payment_processing import PaymentProcessingService
from src.core.enums import Currency, PaymentStatus, ProcessingState
from src.domain.entities import Payment

pytestmark = pytest.mark.asyncio


async def test_processing_does_not_hold_db_lock_during_gateway_call(monkeypatch) -> None:
    payment_id = UUID("12345678-1234-5678-1234-567812345678")
    payment = Payment(
        payment_id=payment_id,
        amount=Decimal("100.00"),
        currency=Currency.USD,
        idempotency_key="key",
        webhook_url="https://example.com/webhook",
    )

    uow = MagicMock()
    uow.payments = AsyncMock()
    uow.webhooks = AsyncMock()
    uow.commit = AsyncMock()
    uow.rollback = AsyncMock()
    uow.payments.get_by_id.side_effect = [payment]
    uow.payments.get_by_id_for_update.return_value = payment

    sleep_called = False

    async def fake_sleep(_: float) -> None:
        nonlocal sleep_called
        sleep_called = True
        assert uow.rollback.await_count == 1

    monkeypatch.setattr(
        "src.application.services.payment_processing.asyncio.sleep",
        fake_sleep,
    )
    monkeypatch.setattr(
        "src.application.services.payment_processing.random.uniform",
        lambda _a, _b: 3.0,
    )
    monkeypatch.setattr(
        "src.application.services.payment_processing.random.random",
        lambda: 0.5,
    )
    monkeypatch.setattr(
        "src.application.services.payment_processing.datetime",
        datetime,
    )

    service = PaymentProcessingService(uow)
    state, result = await service.process_payment_created(payment_id)

    assert sleep_called is True
    assert state is ProcessingState.PROCESSED
    assert result is payment
    assert payment.status is PaymentStatus.SUCCEEDED
    assert payment.processed_at is not None
    uow.payments.update_status.assert_awaited_once_with(payment)
    uow.webhooks.add.assert_awaited_once()
    uow.commit.assert_awaited_once()


async def test_already_processed_payment_is_ackable_without_side_effects() -> None:
    payment = Payment(
        payment_id=UUID("12345678-1234-5678-1234-567812345678"),
        amount=Decimal("10.00"),
        currency=Currency.EUR,
        idempotency_key="key",
        status=PaymentStatus.FAILED,
        processed_at=datetime.now(UTC),
    )
    uow = MagicMock()
    uow.payments = AsyncMock()
    uow.webhooks = AsyncMock()
    uow.rollback = AsyncMock()
    uow.payments.get_by_id.return_value = payment

    state, result = await PaymentProcessingService(uow).process_payment_created(payment.payment_id)

    assert state is ProcessingState.ALREADY_PROCESSED
    assert result is payment
    uow.rollback.assert_awaited_once()
    uow.webhooks.add.assert_not_awaited()
