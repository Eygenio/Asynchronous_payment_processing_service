from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from src.application.dto.outbox import OutboxDispatchResult
from src.application.services.outbox import OutboxService
from src.domain.entities import Outbox
from src.core.enums import OutboxStatus

pytestmark = pytest.mark.asyncio


async def test_dispatch_pending_outbox_returns_dto(monkeypatch) -> None:
    message = Outbox(
        id=uuid4(),
        event_type="payments.new",
        payload={"payment_id": str(uuid4())},
        status=OutboxStatus.PENDING,
    )

    uow = MagicMock()
    uow.outbox = AsyncMock()
    uow.outbox.claim_ready_for_dispatch.return_value = [message]
    uow.commit = AsyncMock()

    publish = AsyncMock()
    monkeypatch.setattr("src.application.services.outbox.publish_payment_new", publish)

    service = OutboxService(uow)
    result = await service.dispatch_pending_outbox()

    assert isinstance(result, OutboxDispatchResult)
    assert result.selected == 1
    assert result.sent == 1
    assert result.failed == 0
