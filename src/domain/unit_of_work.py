from abc import ABC, abstractmethod
from types import TracebackType
from typing import Self

from src.domain.repositories import IOutboxRepository, IPaymentRepository


class IUnitOfWork(ABC):
    payments: IPaymentRepository
    outbox: IOutboxRepository

    @abstractmethod
    async def commit(self) -> None:
        pass

    @abstractmethod
    async def rollback(self) -> None:
        pass

    @abstractmethod
    async def flush(self) -> None:
        pass

    @abstractmethod
    async def __aenter__(self) -> Self:
        pass

    @abstractmethod
    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        pass
