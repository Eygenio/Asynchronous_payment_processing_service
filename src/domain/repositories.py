from abc import ABC, abstractmethod
from collections.abc import Sequence
from datetime import datetime
from uuid import UUID

from src.domain.entities import Outbox, Payment

class IPaymentRepository(ABC):
    @abstractmethod
    async def get_by_id(self, payment_id: UUID) -> Payment | None:
        pass

    @abstractmethod
    async def get_by_id_for_update(self, payment_id: UUID) -> Payment | None:
        pass

    @abstractmethod
    async def get_by_idempotency_key(self, idempotency_key: str) -> Payment | None:
        pass

    @abstractmethod
    async def add(self, payment: Payment) -> Payment:
        pass

    @abstractmethod
    async def refresh(self, payment: Payment) -> None:
        pass

class IOutboxRepository(ABC):
    @abstractmethod
    async def add(self, outbox: Outbox) -> Outbox:
        pass

    @abstractmethod
    async def get_ready_for_dispatch(self, limit: int) -> Sequence[Outbox]:
        pass

    @abstractmethod
    async def mark_published(self, message: Outbox) -> None:
        pass

    @abstractmethod
    async def schedule_retry(self, message: Outbox, attempts: int, next_retry_at: datetime) -> None:
        pass

    @abstractmethod
    async def mark_failed(self, message: Outbox, attempts: int) -> None:
        pass
