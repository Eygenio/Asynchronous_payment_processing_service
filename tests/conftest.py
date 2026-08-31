from decimal import Decimal

import pytest

from src.application.dto.payments import PaymentCreateDTO
from src.core.enums import Currency
from src.domain.entities import Outbox, Payment
from tests.factories import OutboxFactory, PaymentCreateDTOFactory, PaymentFactory


@pytest.fixture
def payment_create_dto() -> PaymentCreateDTO:
    return PaymentCreateDTOFactory.build()


@pytest.fixture
def different_payment_create_dto() -> PaymentCreateDTO:
    return PaymentCreateDTOFactory.build(
        amount=Decimal("101.00"),
        currency=Currency.USD,
        webhook_url=None,
    )


@pytest.fixture
def payment_entity() -> Payment:
    return PaymentFactory.build()


@pytest.fixture
def outbox_entity() -> Outbox:
    return OutboxFactory.build()
