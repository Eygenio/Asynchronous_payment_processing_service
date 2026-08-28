from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status

from src.application.services.outbox import OutboxService
from src.application.services.payment_processing import PaymentProcessingService
from src.application.services.payments import PaymentService
from src.config.settings import settings
from src.db.db import async_session_maker
from src.domain.unit_of_work import IUnitOfWork
from src.infrastructure.unit_of_work import SQLAlchemyUnitOfWork


async def get_uow() -> AsyncGenerator[IUnitOfWork]:
    async with async_session_maker() as session:
        uow = SQLAlchemyUnitOfWork(session)
        try:
            yield uow
        except Exception:
            await uow.rollback()
            raise
        finally:
            await session.close()


UoWDep = Annotated[IUnitOfWork, Depends(get_uow)]


def get_payment_service(uow: UoWDep) -> PaymentService:
    return PaymentService(uow)


PaymentServiceDep = Annotated[PaymentService, Depends(get_payment_service)]


def get_outbox_service(uow: UoWDep) -> OutboxService:
    return OutboxService(uow)


OutboxServiceDep = Annotated[OutboxService, Depends(get_outbox_service)]


def get_payment_processing_service(uow: UoWDep) -> PaymentProcessingService:
    return PaymentProcessingService(uow)


PaymentProcessingServiceDep = Annotated[
    PaymentProcessingService, Depends(get_payment_processing_service)
]


async def verify_api_key(
    api_key: Annotated[str | None, Header(alias="X-API-Key")] = None,
) -> None:
    if not api_key or api_key != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED if not api_key else status.HTTP_403_FORBIDDEN,
            detail="Invalid API key",
        )


ApiKeyAuth = Depends(verify_api_key)
