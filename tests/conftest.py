import asyncio
from collections.abc import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from faker import Faker

from src.app import app
from src.domain.entities import Payment
from src.domain.unit_of_work import IUnitOfWork
from src.presentation.dependencies import get_uow
from src.common.enums import Currency, PaymentStatus

fake = Faker()

@pytest.fixture
def api_client() -> TestClient:
    return TestClient(app)

@pytest.fixture
def sample_payment_data() -> dict:
    return {
        "amount": "100.00",
        "currency": "USD",
        "description": "Test payment",
        "metadata": {"key": "value"},
        "webhook_url": "https://example.com/webhook",
    }

@pytest.fixture
def mock_uow() -> IUnitOfWork:
    uow = MagicMock(spec=IUnitOfWork)
    uow.payments = AsyncMock()
    uow.outbox = AsyncMock()
    uow.commit = AsyncMock()
    uow.rollback = AsyncMock()
    uow.flush = AsyncMock()
    return uow

@pytest.fixture(autouse=True)
def override_get_uow(mock_uow: IUnitOfWork) -> Generator[None, None, None]:
    async def _override() -> AsyncGenerator[IUnitOfWork, None]:
        yield mock_uow

    app.dependency_overrides[get_uow] = _override
    yield
    app.dependency_overrides.pop(get_uow, None)
