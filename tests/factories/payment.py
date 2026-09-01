from decimal import Decimal
from uuid import uuid4

import factory

from src.application.dto.payments import PaymentCreateDTO
from src.core.enums import Currency, PaymentStatus
from src.domain.entities import Payment


class PaymentFactory(factory.Factory):
    class Meta:
        model = Payment

    payment_id = factory.LazyFunction(uuid4)
    amount = factory.Faker("pydecimal", left_digits=3, right_digits=2, positive=True)
    currency = Currency.USD
    idempotency_key = factory.LazyFunction(lambda: str(uuid4()))
    description = factory.Faker("sentence", nb_words=4)
    metadata_ = factory.LazyFunction(dict)
    status = PaymentStatus.PENDING
    webhook_url = factory.Faker("url")
    created_at = None
    processed_at = None


class PaymentCreateDTOFactory(factory.Factory):
    class Meta:
        model = PaymentCreateDTO

    amount = factory.LazyFunction(lambda: Decimal("100.00"))
    currency = Currency.USD
    description = factory.Faker("sentence", nb_words=4)
    metadata = factory.LazyAttribute(lambda _: {"source": "test"})
    webhook_url = factory.Faker("url")


class PaymentPayloadFactory(factory.DictFactory):
    amount = factory.LazyFunction(lambda: "100.00")
    currency = Currency.USD.value
    description = factory.Faker("sentence", nb_words=4)
    metadata = factory.LazyAttribute(lambda _: {"source": "e2e"})
    webhook_url = "https://example.com/webhook"
