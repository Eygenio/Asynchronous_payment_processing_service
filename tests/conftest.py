from collections.abc import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock

import pytest
from faker import Faker
from fastapi.testclient import TestClient

from src.app import app
from src.application.services.payments import PaymentService
from src.domain.unit_of_work import IUnitOfWork
from src.presentation.dependencies import get_uow

fake = Faker()


@pytest.fixture
def api_client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def service(mock_uow: IUnitOfWork) -> PaymentService:
    return PaymentService(mock_uow)


@pytest.fixture
def mock_uow() -> MagicMock:
    uow = MagicMock(spec=IUnitOfWork)
    uow.payments = AsyncMock()
    uow.outbox = AsyncMock()
    uow.commit = AsyncMock()
    uow.rollback = AsyncMock()
    uow.flush = AsyncMock()
    return uow


@pytest.fixture(autouse=True)
def override_get_uow(mock_uow: MagicMock) -> Generator[None]:
    async def _override() -> AsyncGenerator[IUnitOfWork]:
        yield mock_uow

    app.dependency_overrides[get_uow] = _override
    yield
    app.dependency_overrides.pop(get_uow, None)


@pytest.fixture
def sample_payment_data() -> dict[str, object]:
    return {
        "amount": "100.00",
        "currency": "USD",
        "description": "Test payment",
        "metadata": {"key": "value"},
        "webhook_url": "https://example.com/webhook",
    }
