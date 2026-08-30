from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from src.application.services.payments import PaymentService
from src.domain.unit_of_work import IUnitOfWork


@pytest.fixture
def mock_uow() -> IUnitOfWork:
    return SimpleNamespace(
        payments=SimpleNamespace(
            add=AsyncMock(),
            get_by_id=AsyncMock(),
            get_by_id_for_update=AsyncMock(),
            get_by_idempotency_key=AsyncMock(),
            refresh=AsyncMock(),
            update_status=AsyncMock(),
        ),
        outbox=SimpleNamespace(
            add=AsyncMock(),
            claim_ready_for_dispatch=AsyncMock(),
            mark_published=AsyncMock(),
            schedule_retry=AsyncMock(),
            mark_failed=AsyncMock(),
        ),
        webhooks=SimpleNamespace(add=AsyncMock()),
        commit=AsyncMock(),
        rollback=AsyncMock(),
        flush=AsyncMock(),
    )


@pytest.fixture
def service(mock_uow: IUnitOfWork) -> PaymentService:
    return PaymentService(mock_uow)
