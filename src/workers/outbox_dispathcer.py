import asyncio
import logging

from src.db.db import async_session_maker
from src.infrastructure.unit_of_work import SQLAlchemyUnitOfWork
from src.application.services.outbox import OutboxService
from src.rabbit.broker import broker, create_rabbit

logger = logging.getLogger(__name__)

DISPATCH_BATCH_SIZE = 100
DISPATCH_POLL_INTERVAL_SECONDS = 1.0
DISPATCH_ERROR_BACKOFF_SECONDS = 3.0

async def run_outbox_dispatcher() -> None:
    async with broker:
        await create_rabbit()
        logger.info("Outbox dispatcher started")
        while True:
            try:
                async with async_session_maker() as session:
                    uow = SQLAlchemyUnitOfWork(session)
                    stats = await OutboxService(uow).dispatch_pending_outbox(
                        limit=DISPATCH_BATCH_SIZE,
                    )
                    if stats["selected"] > 0:
                        logger.info("Outbox dispatch stats: %s", stats)
                await asyncio.sleep(DISPATCH_POLL_INTERVAL_SECONDS)
            except Exception:
                logger.exception("Outbox dispatcher iteration failed")
                await asyncio.sleep(DISPATCH_ERROR_BACKOFF_SECONDS)

if __name__ == "__main__":
    asyncio.run(run_outbox_dispatcher())
