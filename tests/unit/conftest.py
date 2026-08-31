import pytest

from src.application.services.outbox import OutboxService
from src.application.services.payment_processing import PaymentProcessingService
from src.application.services.payments import PaymentService
from tests.fakes import InMemoryUnitOfWork


@pytest.fixture
def uow() -> InMemoryUnitOfWork:
    return InMemoryUnitOfWork()


@pytest.fixture
def payment_service(uow: InMemoryUnitOfWork) -> PaymentService:
    return PaymentService(uow)


@pytest.fixture
def payment_processing_service(uow: InMemoryUnitOfWork) -> PaymentProcessingService:
    return PaymentProcessingService(uow)


@pytest.fixture
def outbox_service(uow: InMemoryUnitOfWork) -> OutboxService:
    return OutboxService(uow)
