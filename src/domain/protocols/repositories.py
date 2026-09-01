from collections.abc import Sequence
from datetime import datetime
from typing import Protocol
from uuid import UUID

from src.domain.entities import Outbox, Payment, WebhookOutbox


class PaymentRepositoryProtocol(Protocol):
    async def get_by_id(self, payment_id: UUID) -> Payment | None:
        pass

    async def get_by_id_for_update(self, payment_id: UUID) -> Payment | None:
        pass

    async def get_by_idempotency_key(self, idempotency_key: str) -> Payment | None:
        pass

    async def add(self, payment: Payment) -> Payment:
        pass

    async def refresh(self, payment: Payment) -> None:
        pass

    async def update_status(self, payment: Payment) -> None:
        pass


class OutboxRepositoryProtocol(Protocol):
    async def get_by_id(self, message_id: UUID) -> Outbox | None:
        pass

    async def add(self, outbox: Outbox) -> Outbox:
        pass

    async def claim_ready_for_dispatch(
        self,
        limit: int,
        lease_until: datetime,
    ) -> Sequence[Outbox]:
        pass

    async def mark_published(self, message: Outbox) -> None:
        pass

    async def schedule_retry(
        self,
        message: Outbox,
        attempts: int,
        next_retry_at: datetime,
    ) -> None:
        pass

    async def mark_failed(self, message: Outbox, attempts: int) -> None:
        pass


class WebhookOutboxRepositoryProtocol(Protocol):
    async def add(self, delivery: WebhookOutbox) -> WebhookOutbox:
        pass

    async def claim_ready(
        self,
        limit: int,
        lease_until: datetime,
    ) -> Sequence[WebhookOutbox]:
        pass

    async def mark_delivered(self, delivery: WebhookOutbox) -> None:
        pass

    async def schedule_retry(
        self,
        delivery: WebhookOutbox,
        attempts: int,
        next_attempt_at: datetime,
        error: str,
    ) -> None:
        pass

    async def mark_failed(
        self,
        delivery: WebhookOutbox,
        attempts: int,
        error: str,
    ) -> None:
        pass
