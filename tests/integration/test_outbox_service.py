import pytest

from src.application.services.outbox import OutboxService
from src.core.enums import OutboxStatus

pytestmark = pytest.mark.integration


async def test_outbox_service_dispatches_pending_message_with_real_repository(
    integration_uow,
    integration_session_factory,
    outbox_entity,
) -> None:
    message = outbox_entity
    message.status = OutboxStatus.PENDING
    await integration_uow.outbox.add(message)
    await integration_uow.commit()

    published: list[tuple[dict, str | None]] = []

    async def publisher(payload, message_id):
        published.append((payload, message_id))

    service = OutboxService(
        integration_uow,
        session_factory=integration_session_factory,
        publisher=publisher,
        dlq_publisher=publisher,
    )

    result = await service.dispatch_pending_outbox()

    assert result.selected == 1
    assert result.sent == 1
    assert result.failed == 0
    assert published == [(message.payload, str(message.id))]

    stored = await integration_uow.outbox.get_by_id(message.id)
    assert stored is not None
    assert stored.status is OutboxStatus.PUBLISHED
