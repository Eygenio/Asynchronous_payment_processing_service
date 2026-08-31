from datetime import UTC, datetime

import pytest

from src.application.services.payment_processing import PaymentProcessingService
from src.core.enums import PaymentStatus, ProcessingState, WebhookDeliveryStatus
from src.domain.entities import Payment
from src.infrastructure.unit_of_work import SQLAlchemyUnitOfWork

pytestmark = pytest.mark.integration


async def test_processing_commits_status_and_webhook_with_real_repositories(
    integration_uow: SQLAlchemyUnitOfWork,
    payment_entity: Payment,
) -> None:
    payment = payment_entity
    payment.webhook_url = "https://example.com/webhook"
    await integration_uow.payments.add(payment)
    await integration_uow.commit()

    processed_at = datetime(2026, 8, 31, 12, 0, tzinfo=UTC)

    async def no_wait(_delay: float) -> None:
        return None

    service = PaymentProcessingService(
        integration_uow,
        sleep=no_wait,
        random_delay=lambda _min, _max: 0,
        success_probability=lambda: 0.5,
        now=lambda: processed_at,
    )

    state, result = await service.process_payment_created(payment.payment_id)

    stored = await integration_uow.payments.get_by_id(payment.payment_id)

    assert state is ProcessingState.PROCESSED
    assert result is not None
    assert result.status is PaymentStatus.SUCCEEDED
    assert result.processed_at == processed_at
    assert stored is not None
    assert stored.status is PaymentStatus.SUCCEEDED

    deliveries = await integration_uow.webhooks.claim_ready(10, processed_at)
    assert len(deliveries) == 1
    assert deliveries[0].status is WebhookDeliveryStatus.PROCESSING
