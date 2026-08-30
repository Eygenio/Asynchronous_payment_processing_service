from unittest.mock import AsyncMock

from src.application.dto.outbox import OutboxDispatchResult
from src.application.services.outbox import OutboxService

from tests.factories import outbox


class AsyncSessionContext:
    def __init__(self, session) -> None:
        self.session = session

    async def __aenter__(self):
        return self.session

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        return None


async def test_dispatch_pending_outbox_returns_dto(mock_uow) -> None:
    message = outbox()
    mock_uow.outbox.claim_ready_for_dispatch.return_value = [message]

    update_uow = type("Uow", (), {})()
    update_uow.outbox = type("Outbox", (), {})()
    update_uow.outbox.mark_published = AsyncMock()
    update_uow.commit = AsyncMock()

    publish = AsyncMock()
    session = object()

    service = OutboxService(
        mock_uow,
        session_maker=lambda: AsyncSessionContext(session),
        uow_factory=lambda _: update_uow,
        publish_new=publish,
    )

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
