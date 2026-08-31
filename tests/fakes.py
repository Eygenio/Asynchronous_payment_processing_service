from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from src.core.enums import OutboxStatus
from src.domain.entities import Outbox, Payment, WebhookOutbox


class InMemoryPaymentRepository:
    def __init__(self) -> None:
        self.items: dict[UUID, Payment] = {}

    async def get_by_id(self, payment_id: UUID) -> Payment | None:
        return self.items.get(payment_id)

    async def get_by_id_for_update(self, payment_id: UUID) -> Payment | None:
        return self.items.get(payment_id)

    async def get_by_idempotency_key(self, idempotency_key: str) -> Payment | None:
        return next(
            (payment for payment in self.items.values() if payment.idempotency_key == idempotency_key),
            None,
        )

    async def add(self, payment: Payment) -> Payment:
        payment.payment_id = payment.payment_id or uuid4()
        payment.created_at = payment.created_at or datetime.now(UTC)
        self.items[payment.payment_id] = payment
        return payment

    async def refresh(self, payment: Payment) -> None:
        return None

    async def update_status(self, payment: Payment) -> None:
        if payment.payment_id is None:
            raise ValueError("payment_id is None")
        self.items[payment.payment_id] = payment


class InMemoryOutboxRepository:
    def __init__(self) -> None:
        self.items: dict[UUID, Outbox] = {}

    async def add(self, outbox: Outbox) -> Outbox:
        outbox.id = outbox.id or uuid4()
        outbox.created_at = outbox.created_at or datetime.now(UTC)
        self.items[outbox.id] = outbox
        return outbox

    async def claim_ready_for_dispatch(
        self,
        limit: int,
        lease_until: datetime,
    ) -> Sequence[Outbox]:
        messages = [
            message
            for message in self.items.values()
            if message.status is OutboxStatus.PENDING
        ][:limit]
        for message in messages:
            message.status = OutboxStatus.PROCESSING
            message.locked_until = lease_until
        return messages

    async def mark_published(self, message: Outbox) -> None:
        message.status = OutboxStatus.PUBLISHED
        message.published_at = datetime.now(UTC)
        message.locked_until = None

    async def schedule_retry(self, message: Outbox, attempts: int, next_retry_at: datetime) -> None:
        message.status = OutboxStatus.PENDING
        message.retry_count = attempts
        message.backoff_delay = next_retry_at
        message.locked_until = None

    async def mark_failed(self, message: Outbox, attempts: int) -> None:
        message.status = OutboxStatus.FAILED
        message.retry_count = attempts
        message.locked_until = None


class InMemoryWebhookOutboxRepository:
    def __init__(self) -> None:
        self.items: dict[UUID, WebhookOutbox] = {}

    async def add(self, delivery: WebhookOutbox) -> WebhookOutbox:
        delivery.id = delivery.id or uuid4()
        delivery.created_at = delivery.created_at or datetime.now(UTC)
        self.items[delivery.id] = delivery
        return delivery

    async def claim_ready(self, limit: int, lease_until: datetime) -> Sequence[WebhookOutbox]:
        return []

    async def mark_delivered(self, delivery: WebhookOutbox) -> None:
        delivery.delivered_at = datetime.now(UTC)

    async def schedule_retry(
        self,
        delivery: WebhookOutbox,
        attempts: int,
        next_attempt_at: datetime,
        error: str,
    ) -> None:
        delivery.retry_count = attempts
        delivery.next_attempt_at = next_attempt_at
        delivery.last_error = error

    async def mark_failed(self, delivery: WebhookOutbox, attempts: int, error: str) -> None:
        delivery.retry_count = attempts
        delivery.last_error = error


class InMemoryUnitOfWork:
    def __init__(self) -> None:
        self.payments = InMemoryPaymentRepository()
        self.outbox = InMemoryOutboxRepository()
        self.webhooks = InMemoryWebhookOutboxRepository()
        self.commit_count = 0
        self.rollback_count = 0
        self.flush_count = 0

    async def commit(self) -> None:
        self.commit_count += 1

    async def rollback(self) -> None:
        self.rollback_count += 1

    async def flush(self) -> None:
        self.flush_count += 1

    async def __aenter__(self) -> "InMemoryUnitOfWork":
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if exc_type:
            await self.rollback()
