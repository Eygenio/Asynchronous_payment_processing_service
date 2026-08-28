from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from src.application.dto.outbox import OutboxDispatchResult
from src.application.services.outbox import OutboxService
from src.core.enums import OutboxStatus
from src.domain.entities import Outbox

pytestmark = pytest.mark.asyncio


async def test_dispatch_pending_outbox_returns_dto(monkeypatch) -> None:
    message = Outbox(
        id=uuid4(),
        event_type="payments.new",
        payload={"payment_id": str(uuid4())},
        status=OutboxStatus.PENDING,
    )

    main_uow = MagicMock()
    main_uow.outbox = AsyncMock()
    main_uow.outbox.claim_ready_for_dispatch.return_value = [message]
    main_uow.commit = AsyncMock()

    update_uow = MagicMock()
    update_uow.outbox = AsyncMock()
    update_uow.outbox.mark_published = AsyncMock()
    update_uow.outbox.schedule_retry = AsyncMock()
    update_uow.outbox.mark_failed = AsyncMock()
    update_uow.commit = AsyncMock()

    fake_session = AsyncMock()
    fake_session_cm = MagicMock()
    fake_session_cm.__aenter__ = AsyncMock(return_value=fake_session)
    fake_session_cm.__aexit__ = AsyncMock(return_value=None)
    fake_async_session_maker = MagicMock(return_value=fake_session_cm)

    fake_uow_cls = MagicMock(return_value=update_uow)

    monkeypatch.setattr(
        "src.application.services.outbox.async_session_maker",
        fake_async_session_maker,
    )
    monkeypatch.setattr(
        "src.application.services.outbox.SQLAlchemyUnitOfWork",
        fake_uow_cls,
    )

    publish = AsyncMock()
    monkeypatch.setattr("src.application.services.outbox.publish_payment_new", publish)

    service = OutboxService(main_uow)
    result = await service.dispatch_pending_outbox()

    assert isinstance(result, OutboxDispatchResult)
    assert result.selected == 1
    assert result.sent == 1
    assert result.failed == 0

    publish.assert_awaited_once_with(
        message.payload,
        message_id=str(message.id),
    )

    update_uow.outbox.mark_published.assert_awaited_once_with(message)
    update_uow.commit.assert_awaited_once()