import asyncio
from unittest.mock import AsyncMock

from src.application.services.payment_processing import PaymentProcessingService
from src.core.enums import PaymentStatus, ProcessingState

from tests.factories import payment


async def test_processing_does_not_hold_db_lock_during_gateway_call(monkeypatch) -> None:
    entity = payment(webhook_url="https://example.com/webhook")
    uow = type("Uow", (), {})()
    uow.payments = type("Payments", (), {})()
    uow.webhooks = type("Webhooks", (), {})()
    uow.payments.get_by_id = AsyncMock(return_value=entity)
    uow.payments.get_by_id_for_update = AsyncMock(return_value=entity)
    uow.payments.update_status = AsyncMock()
    uow.webhooks.add = AsyncMock()
    uow.commit = AsyncMock()
    uow.rollback = AsyncMock()

    async def fake_sleep(_: float) -> None:
        assert uow.rollback.await_count == 1

    monkeypatch.setattr(asyncio, "sleep", fake_sleep)
    monkeypatch.setattr(
        "src.application.services.payment_processing.random.uniform",
        lambda _a, _b: 3.0,
    )
    monkeypatch.setattr(
        "src.application.services.payment_processing.random.random",
        lambda: 0.5,
    )

    state, result = await PaymentProcessingService(uow).process_payment_created(entity.payment_id)

    assert state is ProcessingState.PROCESSED
    assert result is entity
    assert entity.status is PaymentStatus.SUCCEEDED
    assert entity.processed_at is not None
    uow.payments.update_status.assert_awaited_once_with(entity)
    uow.webhooks.add.assert_awaited_once()
    uow.commit.assert_awaited_once()


async def test_already_processed_payment_is_ackable_without_side_effects() -> None:
    entity = payment(status=PaymentStatus.FAILED, processed_at=payment().created_at)
    uow = type("Uow", (), {})()
    uow.payments = type("Payments", (), {})()
    uow.webhooks = type("Webhooks", (), {})()
    uow.payments.get_by_id = AsyncMock(return_value=entity)
    uow.rollback = AsyncMock()
    uow.webhooks.add = AsyncMock()

    state, result = await PaymentProcessingService(uow).process_payment_created(entity.payment_id)

    assert state is ProcessingState.ALREADY_PROCESSED
    assert result is entity
    uow.rollback.assert_awaited_once()
    uow.webhooks.add.assert_not_awaited()
