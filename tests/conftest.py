from decimal import Decimal

import pytest

from src.core.enums import Currency
from tests.factories import OutboxFactory, PaymentCreateDTOFactory, PaymentFactory


@pytest.fixture
def payment_create_dto():
    return PaymentCreateDTOFactory.build()


@pytest.fixture
def different_payment_create_dto():
    return PaymentCreateDTOFactory.build(
        amount=Decimal("101.00"),
        currency=Currency.USD,
        webhook_url=None,
    )


@pytest.fixture
def payment_entity():
    return PaymentFactory.build()


@pytest.fixture
def outbox_entity():
    return OutboxFactory.build()
