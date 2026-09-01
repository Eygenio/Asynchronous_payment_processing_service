from unittest.mock import AsyncMock

import pytest

from src.application.services.outbox import OutboxService
from src.core.enums import OutboxStatus
from src.domain.entities import Outbox
from src.infrastructure.unit_of_work import SQLAlchemyUnitOfWork

pytestmark = pytest.mark.integration


async def test_outbox_service_with_real_repository(
    outbox_service: OutboxService,
    outbox_publisher: AsyncMock,
    integration_uow: SQLAlchemyUnitOfWork,
    outbox_entity: Outbox,
) -> None:
    message = outbox_entity
    message.status = OutboxStatus.PENDING
    await integration_uow.outbox.add(message)
    await integration_uow.commit()

    result = await outbox_service.dispatch_pending_outbox()

    assert result.selected == 1
    assert result.sent == 1
    assert result.failed == 0

    outbox_publisher.assert_awaited_once_with(
        message.payload,
        str(message.id),
    )

    stored = await integration_uow.outbox.get_by_id(message.id)
    assert stored is not None
    assert stored.status is OutboxStatus.PUBLISHED
