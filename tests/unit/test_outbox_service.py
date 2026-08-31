import pytest

from src.application.services.outbox import OutboxService
from src.core.enums import OutboxStatus
from src.domain.entities import Outbox
from tests.fakes import InMemoryUnitOfWork

pytestmark = pytest.mark.unit


class AsyncContext:
    def __init__(self, value) -> None:
        self.value = value

    async def __aenter__(self) -> None:
        return self.value

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        return None


async def test_dispatch_pending_outbox_publishes_message(
    uow: InMemoryUnitOfWork,
    outbox_entity: Outbox,
) -> None:
    message = outbox_entity
    message.status = OutboxStatus.PENDING
    await uow.outbox.add(message)
    published: list[tuple[dict, str | None]] = []

    async def publisher(payload, message_id):
        published.append((payload, message_id))

    service = OutboxService(
        uow,
        session_factory=lambda: AsyncContext(object()),
        uow_factory=lambda _session: uow,
        publisher=publisher,
        dlq_publisher=publisher,
    )

    result = await service.dispatch_pending_outbox()

    assert result.selected == 1
    assert result.sent == 1
    assert result.failed == 0
    assert message.status is OutboxStatus.PUBLISHED
    assert published == [(message.payload, str(message.id))]
    assert uow.commit_count == 2
