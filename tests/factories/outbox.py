from uuid import uuid4

import factory

from src.core.enums import OutboxStatus
from src.domain.entities import Outbox


class OutboxFactory(factory.Factory):
    class Meta:
        model = Outbox

    event_type = "payments.new"
    payload = factory.LazyFunction(lambda: {"payment_id": str(uuid4())})
    status = OutboxStatus.PENDING
    retry_count = 0
    id = factory.LazyFunction(uuid4)
    backoff_delay = None
    locked_until = None
    published_at = None
    created_at = None
