from types import TracebackType
from typing import Self

from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.unit_of_work import IUnitOfWork
from src.infrastructure.repositories.outbox import OutboxRepository
from src.infrastructure.repositories.payments import PaymentRepository
from src.infrastructure.repositories.webhook_outbox import WebhookOutboxRepository


class SQLAlchemyUnitOfWork(IUnitOfWork):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self.payments = PaymentRepository(session)
        self.outbox = OutboxRepository(session)
        self.webhooks = WebhookOutboxRepository(session)

    async def commit(self) -> None:
        await self._session.commit()

    async def rollback(self) -> None:
        await self._session.rollback()

    async def flush(self) -> None:
        await self._session.flush()

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        if exc_type:
            await self.rollback()
        else:
            await self.commit()
