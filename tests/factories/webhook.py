from uuid import uuid4

import factory

from src.domain.entities import WebhookOutbox


class WebhookOutboxFactory(factory.Factory):
    class Meta:
        model = WebhookOutbox

    payment_id = factory.LazyFunction(uuid4)
    target_url = "https://example.com/webhook"
    payload = factory.LazyFunction(lambda: {"status": "succeeded"})
    id = factory.LazyFunction(uuid4)
